"""Ablation du pipeline de traitement des questions, sur le DEV uniquement.

Configurations cumulatives :
  baseline          BM25 historique (src/demo/repondre.py, inchangé)
  + mots vides      nouvelles listes data/lexiques/, sans normalisation
  + normalisation   minuscules/accents (FR), أإآ ة ى diacritiques tatweel (AR)
  + SymSpell        correction orthographique
  + synonymes       expansion par data/dev/synonymes_juridiques_v1.csv
  pipeline complet  + langue 4 voies, translittération arabizi, lexiques tunisien/sigles,
                    racinisation arabe
Mesures (seuil 9,085 inchangé) par langue de la question (colonne `langue` du dev) :
R@1, R@5, abstentions à tort, refus hors périmètre ; plus R@1/R@5 sur les questions
avec fautes (graine 2026, mêmes fautes que evaluer_correction_dev.py).
Aucun fichier de data/test_locked/ n'est lu.

Usage : python -X utf8 src/evaluation/evaluer_pipeline_dev.py --rapports reports/pipeline_dev
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RACINE), str(RACINE / "src" / "demo"), str(RACINE / "src" / "evaluation")]
import repondre  # noqa: E402
from baseline_bm25 import lire  # noqa: E402
from evaluer_correction_dev import DEV, GRAINE, bruiter  # noqa: E402
from src.pipeline.traitement import Config, Pipeline  # noqa: E402

CONFIGS = [
    Config(True, False, False, False, False, "+ mots vides"),
    Config(True, True, False, False, False, "+ normalisation"),
    Config(True, True, True, False, False, "+ SymSpell"),
    Config(True, True, True, True, False, "+ synonymes"),
    Config(True, True, True, True, True, "pipeline complet"),
    # Diagnostic : tout le pipeline, mais l'arabizi reste traité comme du français.
    Config(True, True, True, True, True, "complet sans translittération", arabizi=False),
]
LANGUES = ["fr", "tun", "ar", "toutes"]   # libellés de la colonne `langue` du dev


def systemes():
    historique = repondre.charger()

    def baseline(q):
        return historique[repondre.detecter_langue(q)].repondre(q, k=5)
    yield "baseline", baseline
    for cfg in CONFIGS:
        p = Pipeline(cfg)
        yield cfg.nom, (lambda q, p=p: p.repondre(q, k=5))


def mesurer(fonction, questions, champ):
    lignes = []
    for q in questions:
        r = fonction(q[champ])
        labels = [c["article"] for c in r["candidats"]]
        gold = q["article_reference"].strip()
        lignes.append({"id": q["id"], "langue": q["langue"], "dans": q["type"] == "dans_perimetre",
                       "abstention": r["abstention"], "top1": labels[:1] == [gold] if gold else False,
                       "top5": gold in labels, "articles": " | ".join(labels)})
    resume = {}
    for langue in LANGUES:
        sel = [l for l in lignes if langue == "toutes" or l["langue"] == langue]
        dans = [l for l in sel if l["dans"]]
        hors = [l for l in sel if not l["dans"]]
        resume[langue] = {
            "n_dans": len(dans), "n_hors": len(hors),
            "r1": sum(l["top1"] for l in dans), "r5": sum(l["top5"] for l in dans),
            "abst_tort": sum(l["abstention"] for l in dans),
            "refus_hors": sum(l["abstention"] for l in hors),
        }
    return resume, lignes


def cellule(m, cle):
    n = m["n_dans"] if cle != "refus_hors" else m["n_hors"]
    return f"{m[cle]}/{n}" if n else "—"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapports", type=Path, required=True)
    args = parser.parse_args()
    dossier = args.rapports if args.rapports.is_absolute() else RACINE / args.rapports
    if dossier.exists() and any(dossier.iterdir()):
        raise SystemExit(f"{dossier} existe déjà et n'est pas vide : choisir un dossier neuf.")

    rng = random.Random(GRAINE)
    questions = lire(DEV)
    for q in questions:
        q["question_fautes"] = bruiter(q["question"], repondre.detecter_langue(q["question"]), rng)

    tableau, details = [], []
    for nom, fonction in systemes():
        propre, lignes = mesurer(fonction, questions, "question")
        fautes, _ = mesurer(fonction, questions, "question_fautes")
        ligne = {"configuration": nom}
        for langue in LANGUES:
            m = propre[langue]
            for cle, titre in [("r1", "R@1"), ("r5", "R@5"), ("abst_tort", "abst_tort"),
                               ("refus_hors", "refus_hors")]:
                ligne[f"{langue}_{titre}"] = cellule(m, cle)
        ligne["fautes_R@1"] = cellule(fautes["toutes"], "r1")
        ligne["fautes_R@5"] = cellule(fautes["toutes"], "r5")
        ligne["fautes_refus_hors"] = cellule(fautes["toutes"], "refus_hors")
        tableau.append(ligne)
        details += [{"configuration": nom, **l} for l in lignes]

    dossier.mkdir(parents=True, exist_ok=True)
    for nom, lignes in [("tableau_pipeline_dev.csv", tableau), ("details_pipeline_dev.csv", details)]:
        with open(dossier / nom, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0]))
            w.writeheader()
            w.writerows(lignes)
    with open(dossier / "evaluation_pipeline_dev.json", "w", encoding="utf-8") as f:
        json.dump({"jeu": "questions_dev_v2 (développement, non indépendant)", "graine_fautes": GRAINE,
                   "seuil_abstention": repondre.SEUIL_SCORE_MIN, "resultats": tableau},
                  f, ensure_ascii=False, indent=2)
    for l in tableau:
        print(l)
    print(f"Rapports : {dossier}")


if __name__ == "__main__":
    main()
