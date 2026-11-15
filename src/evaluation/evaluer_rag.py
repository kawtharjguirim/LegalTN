"""Compare les variantes de prompting du RAG (P0, P1, P2, P3, P2V) sur le jeu de DÉVELOPPEMENT.

Lit uniquement data/dev/ (empreinte vérifiée), refuse data/test_locked/.
Les deux exemples few-shot de P3 (D01 dans le périmètre, D14 hors périmètre) sont EXCLUS de
l'évaluation de toutes les variantes, pour que les comparaisons portent sur les mêmes questions.
Leur sortie attendue reprend la réponse de référence déjà écrite dans le dev (aucune donnée créée).

Mesures automatiques (pas de jugement de fidélité ici : grille humaine à faire par l'équipe) :
  dans le périmètre : citation exacte (référence parmi les articles cités), fausse abstention,
                      réponse sans citation, articles inventés (cités mais non fournis / hors corpus)
  hors périmètre    : abstention correcte

Usage :
  python -X utf8 src/evaluation/evaluer_rag.py --rapports reports/silver/rag_dev
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
sys.path.insert(0, str(RACINE / "src"))
import repondre  # noqa: E402
from baseline_bm25 import lire  # noqa: E402
from evaluer_retrieval import DEV_V2, verifier_jeu  # noqa: E402
from rag import rag  # noqa: E402

IDS_EXEMPLES = ("D01", "D14")


def exemples_few_shot(questions, corpus):
    ex = []
    for q in questions:
        if q["id"] not in IDS_EXEMPLES:
            continue
        dans = q["type"] == "dans_perimetre"
        ref = q["article_reference"].strip()
        sortie = {"reponse": q["reponse_attendue"] if dans else "",
                  "articles_cites": [ref] if dans else [], "extrait": "",
                  "abstention": not dans}
        ex.append({"question": q["question"], "passages": rag.passages_bm25(q["question"], corpus),
                   "sortie": sortie})
    return ex


def mesurer(lignes, variante, corpus_labels):
    dans = [l for l in lignes if l["dans_perimetre"]]
    hors = [l for l in lignes if not l["dans_perimetre"]]
    def res(l): return l["sorties"][variante]
    inventes = sum(1 for l in lignes for a in res(l)["articles_cites"]
                   if a not in res(l)["passages"] or a not in corpus_labels)
    hors_corpus = sum(1 for l in lignes for a in res(l)["articles_cites"] if a not in corpus_labels)
    return {
        "n_dans": len(dans), "n_hors": len(hors),
        "citation_exacte": sum(l["reference"] in res(l)["articles_cites"] and not res(l)["abstention"] for l in dans),
        "fausse_abstention": sum(res(l)["abstention"] for l in dans),
        "reponse_sans_citation": sum(not res(l)["abstention"] and not res(l)["articles_cites"] for l in dans),
        "abstention_correcte_hors": sum(res(l)["abstention"] for l in hors),
        "citations_non_fournies": inventes,
        "citations_hors_corpus": hors_corpus,
        "erreurs_llm": sum(bool(res(l).get("erreur")) for l in lignes),
        "json_invalide":sum(res(l).get("json_valide") is False for l in lignes),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeu", default=str(DEV_V2))
    p.add_argument("--modele", default=rag.MODELE_DEFAUT)
    p.add_argument("--rapports", required=True)
    a = p.parse_args()
    jeu = verifier_jeu(a.jeu)
    corpus = repondre.charger()
    labels = {x["article"] for lg in corpus.values() for x in lg.articles}
    questions = list(lire(jeu))
    exemples = exemples_few_shot(questions, corpus)

    lignes, t0 = [], time.time()
    for q in questions:
        if q["id"] in IDS_EXEMPLES:
            continue
        sorties = {}
        for v in ("P0", "P1", "P2", "P3"):
            sorties[v] = rag.repondre_rag(q["question"], corpus, v, a.modele, exemples)
        p2 = sorties["P2"]
        sorties["P2V"] = {**p2, "variante": "P2V", **rag.verifier_citations(
            {k: p2[k] for k in ("reponse", "articles_cites", "extrait", "abstention", "json_valide")},
            [{"article": x} for x in p2["passages"]])}
        lignes.append({"id": q["id"], "langue": q["langue"], "dans_perimetre": q["type"] == "dans_perimetre",
                       "reference": q["article_reference"].strip(), "sorties": sorties})
        print(q["id"], {v: (s["articles_cites"], s["abstention"]) for v, s in sorties.items()}, flush=True)
    duree = time.time() - t0

    groupes = {"toutes": lignes}
    for l in lignes:
        groupes.setdefault(l["langue"], []).append(l)
    resume = {g: {v: mesurer(ls, v, labels) for v in rag.VARIANTES} for g, ls in groupes.items()}
    meta = {"jeu": jeu.name, "sha256_jeu": hashlib.sha256(jeu.read_bytes()).hexdigest(),
            "modele": a.modele, "temperature": 0, "graine": rag.GRAINE, "k_passages": rag.K_PASSAGES,
            "recuperation": "BM25 langue detectee, sans seuil", "exemples_exclus": IDS_EXEMPLES,
            "statut": "developpement_non_independant", "secondes": round(duree)}
    sortie = Path(a.rapports)
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "resultats.json").write_text(json.dumps({"meta": meta, "resume": resume, "questions": lignes},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    for g, d in resume.items():
        for v, m in d.items():
            print(g, v, json.dumps(m))


if __name__ == "__main__":
    main()
