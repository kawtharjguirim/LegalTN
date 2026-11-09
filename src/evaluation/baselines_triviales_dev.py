"""Baselines triviales du retrieval, comparées au BM25, sur le DEV uniquement.

- aléatoire     : 5 articles distincts tirés au hasard dans le corpus de la langue de la
                  question (graine fixe GRAINE), jamais d'abstention ;
- mots communs  : articles classés par nombre de mots distincts partagés avec la question
                  (mêmes jetons que le BM25 historique : minuscules, accents, mots vides),
                  sans pondération ; abstention seulement si aucun mot en commun ;
- BM25 historique et pipeline complet : pour comparaison (seuil 9,085 inchangé).

Mêmes mesures que l'ablation (R@1, R@5, abstentions à tort, refus hors périmètre, par langue).
Aucun fichier de data/test_locked/ n'est lu.

Usage : python -X utf8 src/evaluation/baselines_triviales_dev.py --rapports reports/baselines_triviales_dev
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
from baseline_bm25 import lire, tokens  # noqa: E402
from evaluer_pipeline_dev import LANGUES, cellule, mesurer  # noqa: E402
from src.pipeline.traitement import Pipeline  # noqa: E402

DEV = RACINE / "data" / "dev" / "questions_dev_v2.csv"
GRAINE = 2026
K = 5


def intitules(corpus) -> list[str]:
    return list(dict.fromkeys(a["article"] for a in corpus.articles))


def baseline_aleatoire(historique):
    rng = random.Random(GRAINE)
    labels = {l: intitules(c) for l, c in historique.items()}

    def repondre_q(q):
        tires = rng.sample(labels[repondre.detecter_langue(q)], K)
        return {"abstention": False, "candidats": [{"article": a} for a in tires]}
    return repondre_q


def baseline_mots_communs(historique):
    def repondre_q(q):
        langue = repondre.detecter_langue(q)
        c = historique[langue]
        requete = set(tokens(q, langue))
        scores = {}
        for art, tf in zip(c.articles, c.bm.tf):
            s = len(requete & tf.keys())
            if s > scores.get(art["article"], 0):
                scores[art["article"]] = s
        classes = sorted(scores.items(), key=lambda x: -x[1])   # tri stable : ordre du corpus à égalité
        if not classes:
            return {"abstention": True, "candidats": []}
        return {"abstention": False, "candidats": [{"article": a} for a, _ in classes[:K]]}
    return repondre_q


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapports", type=Path, required=True)
    args = parser.parse_args()
    dossier = args.rapports if args.rapports.is_absolute() else RACINE / args.rapports
    if dossier.exists() and any(dossier.iterdir()):
        raise SystemExit(f"{dossier} existe déjà et n'est pas vide : choisir un dossier neuf.")

    questions = lire(DEV)
    historique = repondre.charger()
    complet = Pipeline()
    systemes = [
        ("aléatoire (graine 2026)", baseline_aleatoire(historique)),
        ("mots communs", baseline_mots_communs(historique)),
        ("BM25 historique (seuil 9,085)", lambda q: historique[repondre.detecter_langue(q)].repondre(q, k=K)),
        ("pipeline complet (seuil 9,085)", lambda q: complet.repondre(q, k=K)),
    ]
    tableau, details = [], []
    for nom, f in systemes:
        resume, lignes = mesurer(f, questions, "question")
        ligne = {"systeme": nom}
        for langue in LANGUES:
            for cle, titre in [("r1", "R@1"), ("r5", "R@5"), ("abst_tort", "abst_tort"),
                               ("refus_hors", "refus_hors")]:
                ligne[f"{langue}_{titre}"] = cellule(resume[langue], cle)
        tableau.append(ligne)
        details += [{"systeme": nom, **l} for l in lignes]

    n_fr, n_ar = (len(intitules(c)) for c in (historique["fr"], historique["ar"]))
    dossier.mkdir(parents=True, exist_ok=True)
    for nom, lignes in [("tableau_baselines_dev.csv", tableau), ("details_baselines_dev.csv", details)]:
        with open(dossier / nom, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0]))
            w.writeheader()
            w.writerows(lignes)
    with open(dossier / "baselines_dev.json", "w", encoding="utf-8") as f:
        json.dump({"jeu": "questions_dev_v2 (développement, non indépendant)", "graine": GRAINE, "k": K,
                   "intitules_distincts": {"fr": n_fr, "ar": n_ar},
                   "rappel5_attendu_aleatoire_fr": round(K / n_fr, 4), "resultats": tableau},
                  f, ensure_ascii=False, indent=2)
    print(f"intitulés distincts : FR {n_fr}, AR {n_ar} ; R@5 attendu au hasard (FR) = {K / n_fr:.4f}")
    for l in tableau:
        print(f"{l['systeme']:32} total R@1 {l['toutes_R@1']:6} R@5 {l['toutes_R@5']:6} "
              f"abst.tort {l['toutes_abst_tort']:6} refus hors {l['toutes_refus_hors']:6} | "
              f"FR R@5 {l['fr_R@5']:6} TUN R@5 {l['tun_R@5']}")


if __name__ == "__main__":
    main()
