"""Audit Gold : hallucinations juridiques, abstention par langue, robustesse INV, écart entre langues.

Chaîne auditée = celle de la démo : recherche hybride BM25 + e5 (3 articles), seuil d'abstention
par langue, puis qwen2.5:3b en citation forcée. Questions : dev v2 (FR, tunisien, hors
périmètre) + traductions AR + paraphrases (``questions_paraphrases_v1.csv``, à valider).
Aucun jeu de test gelé n'est lu.

Mesures :
- hallucinations : article cité qui n'existe pas dans le Code (« inventé ») ; article cité hors des
  extraits fournis, mesuré AVANT le filtre de citation forcée ; réponse sans citation ;
- abstention par langue : fausses abstentions (dans le périmètre), abstentions correctes (hors) ;
- INV : pour chaque perturbation, part des réponses identiques à l'original (premier article de
  la recherche, décision d'abstention, articles cités par le LLM) ; le même calcul entre trois
  répétitions de l'original donne le **bruit de référence** du LLM non déterministe ;
- écart entre langues : question FR et sa traduction AR -> même article ?

Usage : python -X utf8 -m src.audit.audit --sortie reports/gold/audit
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from src.rag import generer
from src.rag.evaluer import questions as questions_dev
from src.rag.evaluer_llm import mentions
from src.rag.recherche import RACINE, Recherche
from src.rag.service import SEUILS, SEUILS_BRUT, SIGNAL, abstenir

from .perturbations import variantes

PARAPHRASES = RACINE / "data/dev/questions_paraphrases_v1.csv"
TRADUCTIONS = RACINE / "data/dev/questions_dev_ar_traduites_v1.csv"
REPETITIONS = 3
K = 3


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def construire_jeu() -> list[dict]:
    """Toutes les requêtes à poser : originaux répétés, perturbations, paraphrases."""
    paraphrases = defaultdict(list)
    for p in lire(PARAPHRASES):
        paraphrases[p["source_id"]].append(p["paraphrase"])
    jeu = []
    for q in questions_dev():
        base = {"source": q["id"], "langue": q["langue"], "dans": q["dans"], "reference": q["reference"]}
        for r in range(REPETITIONS):
            jeu.append({**base, "type": "original", "repetition": r, "question": q["question"]})
        if q["langue"] == "tun":
            continue  # le tunisien est traité à part (palier Gold, point 3)
        for nom, texte in variantes(q["question"], q["langue"], q["dans"]).items():
            jeu.append({**base, "type": nom, "repetition": 0, "question": texte})
        for texte in paraphrases.get(q["id"], []):
            jeu.append({**base, "type": "paraphrase", "repetition": 0, "question": texte})
    return jeu


def interroger(moteur: Recherche, ligne: dict, articles_du_code: set[str]) -> dict:
    """Chaîne de la démo, en gardant la sortie brute du LLM (avant le filtre de citation)."""
    res, sig = moteur.rechercher(ligne["question"], mode="hybride", bilingue=False, k=K)
    langue = sig["langue"]
    abst_recherche = not res or abstenir(sig, langue)
    sortie = {"langue_detectee": langue, "top1": res[0].article if res else "",
              "cos_max": round(sig["cos_max"], 4), "signal": round(sig[SIGNAL], 4), "abstention_recherche": abst_recherche,
              "llm_appele": False, "abstention_llm": None, "citations": "", "cites_brut": "",
              "invente": False, "hors_contexte_brut": False, "sans_citation": False,
              "reponse": "", "latence_s": 0.0, "erreur_llm": ""}
    if abst_recherche:
        sortie["abstention"] = True
        return sortie
    debut = time.perf_counter()
    for essai in range(2):
        try:
            r = generer.repondre(ligne["question"], res, langue, "citation_forcee")
            break
        except Exception as e:  # serveur Ollama momentanément indisponible (mémoire, redémarrage)
            if essai:
                sortie.update({"abstention": True, "erreur_llm": f"{type(e).__name__}: {e}"[:200]})
                return sortie
            time.sleep(10)
    autorises = {x.article.lower() for x in res}
    cites = sorted(set(r["citations"]) | set(mentions(r["brut"])))
    sortie.update({
        "llm_appele": True, "abstention_llm": r["abstention"], "abstention": r["abstention"],
        "citations": " | ".join(sorted(set(r["citations"]))) if not r["abstention"] else "",
        "cites_brut": " | ".join(cites),
        "invente": any(c not in articles_du_code for c in cites),
        "hors_contexte_brut": any(c not in autorises for c in cites),
        "sans_citation": not r["citations"] and generer.ABSTENTION["fr"][:25] not in r["brut"]
                         and generer.ABSTENTION["ar"][:25] not in r["brut"],
        "reponse": r["reponse"], "latence_s": round(time.perf_counter() - debut, 2)})
    return sortie


# ---------------------------------------------------------------------- métriques
def taux(n: int, d: int):
    return round(n / d, 3) if d else None


def signature(l: dict, niveau: str) -> str:
    """Ce qui doit rester invariant : premier article retrouvé, décision, articles cités."""
    if niveau == "recherche":
        return "ABST" if l["abstention_recherche"] else l["top1"]
    if niveau == "decision":
        return "ABST" if l["abstention"] else "REPOND"
    return "ABST" if l["abstention"] else (l["citations"] or "AUCUNE")


def invariance(lignes: list[dict]) -> dict:
    """Part des variantes identiques à l'original (répétition 0), par type et par niveau."""
    ref = {l["source"]: l for l in lignes if l["type"] == "original" and l["repetition"] == 0}
    groupes = defaultdict(list)
    for l in lignes:
        if l["type"] == "original" and l["repetition"] == 0:
            continue
        cle = "bruit_reference (original répété)" if l["type"] == "original" else l["type"]
        groupes[cle].append(l)
    sortie = {}
    for cle, ls in sorted(groupes.items()):
        sortie[cle] = {"n": len(ls)}
        for niveau in ("recherche", "decision", "citations"):
            same = sum(signature(l, niveau) == signature(ref[l["source"]], niveau) for l in ls)
            sortie[cle][niveau] = taux(same, len(ls))
    return sortie


def hallucinations(lignes: list[dict]) -> dict:
    llm = [l for l in lignes if l["llm_appele"]]
    repondu = [l for l in llm if not l["abstention_llm"]]
    hors = [l for l in lignes if not l["dans"]]
    return {
        "reponses_llm": len(llm),
        "article_invente_brut": taux(sum(l["invente"] for l in llm), len(llm)),
        "citation_hors_contexte_brut": taux(sum(l["hors_contexte_brut"] for l in llm), len(llm)),
        "sans_citation_brut": taux(sum(l["sans_citation"] for l in llm), len(llm)),
        "article_invente_affiche": taux(sum(l["invente"] for l in repondu), len(repondu)),
        "hors_perimetre_avec_reponse": taux(sum(not l["abstention"] for l in hors), len(hors)),
    }


def abstention_par_langue(lignes: list[dict]) -> dict:
    orig = [l for l in lignes if l["type"] == "original" and l["repetition"] == 0]
    sortie = {}
    for lg in sorted({l["langue"] for l in orig}):
        dans = [l for l in orig if l["langue"] == lg and l["dans"]]
        hors = [l for l in orig if l["langue"] == lg and not l["dans"]]
        sortie[lg] = {
            "n_dans": len(dans), "n_hors": len(hors),
            "fausse_abstention_recherche": taux(sum(l["abstention_recherche"] for l in dans), len(dans)),
            "fausse_abstention_finale": taux(sum(l["abstention"] for l in dans), len(dans)),
            "reference_citee": taux(sum((not l["abstention"]) and l["reference"].lower() in
                                        l["citations"].split(" | ") for l in dans), len(dans)),
            "abstention_correcte_hors": taux(sum(l["abstention"] for l in hors), len(hors)),
        }
    return sortie


def ecart_langues(lignes: list[dict]) -> dict:
    """Paires question FR / traduction AR (originaux, répétition 0)."""
    orig = {l["source"]: l for l in lignes if l["type"] == "original" and l["repetition"] == 0}
    paires = [(orig[t["source_id"]], orig[t["id"]]) for t in lire(TRADUCTIONS)
              if t["source_id"] in orig and t["id"] in orig]
    def juste(l):
        return (not l["abstention"]) and l["reference"].lower() in l["citations"].split(" | ")
    return {
        "paires": len(paires),
        "meme_premier_article": taux(sum(f["top1"] == a["top1"] for f, a in paires), len(paires)),
        "meme_decision": taux(sum(f["abstention"] == a["abstention"] for f, a in paires), len(paires)),
        "memes_citations": taux(sum(signature(f, "citations") == signature(a, "citations") for f, a in paires), len(paires)),
        "juste_fr_seulement": sum(juste(f) and not juste(a) for f, a in paires),
        "juste_ar_seulement": sum(juste(a) and not juste(f) for f, a in paires),
        "juste_les_deux": sum(juste(f) and juste(a) for f, a in paires),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/audit")
    parser.add_argument("--appareil", default="cpu",
                        help="Appareil de l'encodeur e5 (cpu par défaut : la carte graphique reste au LLM).")
    args = parser.parse_args()
    if not generer.disponible():
        raise SystemExit("Ollama ou qwen2.5:3b indisponible.")
    moteur = Recherche("intfloat/multilingual-e5-base", appareil=args.appareil)
    code = {a["article"].lower() for c in moteur.corpus.values() for a in c.articles}
    jeu = construire_jeu()
    print(f"{len(jeu)} requêtes à poser", flush=True)
    lignes = []
    for k, l in enumerate(jeu, 1):
        lignes.append({**l, **interroger(moteur, l, code)})
        if k % 50 == 0:
            print(f"  {k}/{len(jeu)}", flush=True)

    erreurs = sum(bool(l["erreur_llm"]) for l in lignes)
    if erreurs:
        print(f"ATTENTION : {erreurs} appels au LLM en échec (comptés comme abstentions, voir erreur_llm)")
    resultats = {"modele": generer.MODELE_DEFAUT, "strategie": "citation_forcee", "k_contexte": K,
                 "appels_llm_en_echec": erreurs,
                 "seuils": SEUILS, "seuils_brut": SEUILS_BRUT, "signal": SIGNAL, "n_requetes": len(lignes),
                 "avertissement": "dev déjà consulté ; traductions et paraphrases par Claude, à valider",
                 "hallucinations": hallucinations(lignes), "abstention_par_langue": abstention_par_langue(lignes),
                 "invariance": invariance(lignes), "ecart_langues": ecart_langues(lignes)}
    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "audit_resultats.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    with open(args.sortie / "audit_details.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print(json.dumps({k: resultats[k] for k in ("hallucinations", "ecart_langues")}, ensure_ascii=False, indent=1))
    for cle, v in resultats["invariance"].items():
        print(f"  INV {cle:34s} n={v['n']:3d}  recherche {v['recherche']}  décision {v['decision']}  citations {v['citations']}")
    for lg, v in resultats["abstention_par_langue"].items():
        print(f"  {lg:8s} {v}")


if __name__ == "__main__":
    main()
