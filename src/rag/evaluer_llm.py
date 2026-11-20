"""Évaluation du LLM (Ollama) : 3 stratégies de prompting + résumés à noter à la main.

Questions : dev v2 (FR, tunisien, AR hors périmètre) + 21 questions AR traduites (à valider).
Aucun fichier de data/test_locked n'est lu.

Pour chaque question, le LLM reçoit les 3 premiers articles de la recherche hybride (e5),
**sans** filtre d'abstention de la recherche : on mesure ainsi le comportement du LLM seul,
y compris face à un contexte hors sujet. La colonne ``pipeline_*`` applique en plus le seuil
d'abstention par langue de la démo.

Mesures (température 0, une seule exécution par stratégie ; les sorties varient d'une exécution à l'autre) :
- dans le périmètre : citation au format [Article N], article mentionné en texte libre,
  citation de l'article de référence, citation hors contexte (inventée), abstention à tort,
  réponse dans la langue de la question ;
- hors périmètre : abstention du LLM.

Usage : python -X utf8 -m src.rag.evaluer_llm --sortie reports/silver/llm
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

from . import generer
from .evaluer import questions
from .recherche import RACINE
from .service import SEUILS

RE_MENTION = re.compile(r"(?:article|الفصل)\s+(\d+(?:\s+(?:bis|ter|quater|مكرر))?)", re.IGNORECASE)
K = 3


def mentions(texte: str) -> list[str]:
    """Articles mentionnés en texte libre (« article 79 », « الفصل 79 »)."""
    return [" ".join(m.lower().replace("مكرر", "bis").split()) for m in RE_MENTION.findall(texte)]


def part_arabe(texte: str) -> float:
    lettres = [c for c in texte if c.isalpha()]
    return sum("؀" <= c <= "ۿ" for c in lettres) / len(lettres) if lettres else 0.0


def taux(n: int, d: int):
    return round(n / d, 3) if d else None


def resumer_lignes(lignes: list[dict]) -> dict:
    dans = [l for l in lignes if l["dans"]]
    hors = [l for l in lignes if not l["dans"]]
    repondu = [l for l in dans if not l["abstention_llm"]]
    return {
        "n_dans": len(dans), "n_hors": len(hors),
        "citation_format_strict": taux(sum(bool(l["citations"]) for l in repondu), len(repondu)),
        "article_mentionne": taux(sum(bool(l["mentions"]) for l in repondu), len(repondu)),
        "reference_citee": taux(sum(l["reference_citee"] for l in dans), len(dans)),
        "reference_dans_contexte": taux(sum(l["reference_dans_contexte"] for l in dans), len(dans)),
        "citation_inventee": taux(sum(l["citation_inventee"] for l in repondu), len(repondu)),
        "abstention_a_tort": taux(sum(l["abstention_llm"] for l in dans), len(dans)),
        "abstention_hors_perimetre": taux(sum(l["abstention_llm"] for l in hors), len(hors)),
        "pipeline_abstention_hors": taux(sum(l["pipeline_abstention"] for l in hors), len(hors)),
        "pipeline_abstention_a_tort": taux(sum(l["pipeline_abstention"] for l in dans), len(dans)),
        "langue_respectee": taux(sum(l["langue_respectee"] for l in dans if not l["abstention_llm"]),
                                 len(repondu)),
        "latence_moyenne_s": round(sum(l["latence_s"] for l in lignes) / len(lignes), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/silver/llm")
    parser.add_argument("--modele", default=generer.MODELE_DEFAUT)
    parser.add_argument("--resumes", type=int, default=20, help="Articles à résumer par langue.")
    args = parser.parse_args()
    if not generer.disponible(args.modele):
        raise SystemExit(f"Ollama ou le modèle {args.modele} est indisponible.")

    from .recherche import Recherche

    moteur = Recherche("intfloat/multilingual-e5-base")
    qs = questions()
    contextes = {}
    for q in qs:
        res, sig = moteur.rechercher(q["question"], mode="hybride", bilingue=False, k=K)
        contextes[q["id"]] = (res, sig)

    details, tableau = [], []
    for strategie in generer.STRATEGIES:
        lignes = []
        for q in qs:
            res, sig = contextes[q["id"]]
            langue = sig["langue"]
            debut = time.perf_counter()
            r = generer.repondre(q["question"], res, langue, strategie, modele=args.modele)
            duree = time.perf_counter() - debut
            autorises = {x.article.lower() for x in res}
            citees = set(r["citations"]) | set(mentions(r["brut"]))
            ref = q["reference"].lower()
            arabe_attendu = langue == "ar"
            lignes.append({
                "strategie": strategie, "id": q["id"], "langue": q["langue"], "dans": q["dans"],
                "question": q["question"], "reference": q["reference"],
                "contexte": " | ".join(x.article for x in res),
                "reponse": r["reponse"], "brut": r["brut"],
                "citations": " | ".join(r["citations"]), "mentions": " | ".join(mentions(r["brut"])),
                "abstention_llm": r["abstention"],
                "reference_dans_contexte": bool(ref) and ref in autorises,
                "reference_citee": bool(ref) and not r["abstention"] and ref in citees,
                "citation_inventee": not r["abstention"] and bool(citees - autorises),
                "langue_respectee": (part_arabe(r["brut"]) > 0.5) == arabe_attendu,
                "pipeline_abstention": sig["cos_max"] < SEUILS[langue] or r["abstention"],
                "latence_s": round(duree, 2),
            })
        par_langue = {lg: resumer_lignes([l for l in lignes if l["langue"] == lg])
                      for lg in sorted({l["langue"] for l in lignes})}
        resume = {"strategie": strategie, "global": resumer_lignes(lignes), "par_langue": par_langue}
        tableau.append(resume)
        details += lignes
        g = resume["global"]
        print(f"{strategie:16s} réf. citée {g['reference_citee']} | format strict {g['citation_format_strict']} "
              f"| inventée {g['citation_inventee']} | abst. à tort {g['abstention_a_tort']} "
              f"| abst. hors {g['abstention_hors_perimetre']} | langue {g['langue_respectee']} "
              f"| {g['latence_moyenne_s']} s", flush=True)

    # Résumés en langage clair des articles de référence, à noter à la main (grille 1-5).
    resumes, vus = [], set()
    for q in qs:
        if not q["dans"] or len([r for r in resumes if r["langue"] == ("ar" if q["langue"].startswith("ar") else "fr")]) >= args.resumes:
            continue
        lg = "ar" if q["langue"].startswith("ar") else "fr"
        if (q["reference"], lg) in vus or moteur._index(lg, q["reference"]) is None:
            continue
        vus.add((q["reference"], lg))
        art = moteur.corpus[lg].articles[moteur._index(lg, q["reference"])]
        debut = time.perf_counter()
        texte = generer.resumer(q["reference"], art["texte"], lg, modele=args.modele)
        resumes.append({"article": q["reference"], "langue": lg, "texte_article": art["texte"],
                        "resume": texte, "latence_s": round(time.perf_counter() - debut, 2),
                        "exactitude_1_5": "", "clarte_1_5": "", "commentaire": ""})

    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "prompting_details.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(details[0].keys()))
        w.writeheader()
        w.writerows(details)
    with open(args.sortie / "prompting_resultats.json", "w", encoding="utf-8") as f:
        json.dump({"modele": args.modele, "k_contexte": K, "n_questions": len(qs),
                   "avertissement": "dev déjà consulté ; questions AR traduites à valider ; "
                                    "température 0, une exécution (sorties non déterministes d'une exécution à l'autre)", "strategies": tableau},
                  f, ensure_ascii=False, indent=2)
    with open(args.sortie / "resumes_a_noter.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resumes[0].keys()))
        w.writeheader()
        w.writerows(resumes)
    print(f"{len(resumes)} résumés à noter -> {args.sortie / 'resumes_a_noter.csv'}")


if __name__ == "__main__":
    main()
