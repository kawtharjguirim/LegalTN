"""Évaluation et ablations de la recherche (palier Silver) sur questions de développement.

Jeux : ``questions_dev_v2.csv`` (FR, tunisien, AR hors périmètre) et
``questions_dev_ar_traduites_v1.csv`` (traductions AR des questions FR, à valider).
Aucun fichier de data/test_locked n'est lu.

Configurations : BM25 (Bronze), dense (e5, LaBSE), hybride RRF ; mono- ou bilingue.
Mesures dans le périmètre : R@1, R@5, MRR. Abstention : seuil sur le meilleur cosinus,
choisi par validation croisée « leave-one-out » pour ne pas mesurer sur ce qui a réglé.

Usage : python -X utf8 -m src.rag.evaluer --sortie reports/silver/rag
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from .recherche import RACINE, Recherche, repondre

DEV = RACINE / "data/dev/questions_dev_v2.csv"
DEV_AR = RACINE / "data/dev/questions_dev_ar_traduites_v1.csv"
MODELES = ["intfloat/multilingual-e5-base", "sentence-transformers/LaBSE"]
CONFIGS = [("bm25", False), ("dense", False), ("dense", True), ("hybride", False), ("hybride", True)]


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def questions() -> list[dict]:
    q = [{"id": r["id"], "langue": r["langue"], "dans": r["type"] == "dans_perimetre",
          "question": r["question"], "reference": (r["article_reference"] or "").strip().removesuffix(".0")}
         for r in lire(DEV)]
    q += [{"id": r["id"], "langue": "ar_trad", "dans": True, "question": r["question"],
           "reference": r["article_reference"].strip()} for r in lire(DEV_AR)]
    return q


def seuil_loo(scores: np.ndarray, dans: np.ndarray) -> tuple[np.ndarray, float]:
    """Décision d'abstention de chaque question avec un seuil réglé sans elle.

    Le seuil maximise l'exactitude « répondre si dans le périmètre, s'abstenir sinon »."""
    def meilleur(idx):
        # Seuils candidats : milieux entre scores d'entraînement (aucune fuite de la question
        # mise de côté) ; parmi les seuils ex aequo, le central de la plage optimale.
        s = np.unique(scores[idx])
        candidats = np.concatenate([[s[0] - 1e-6], (s[:-1] + s[1:]) / 2, [s[-1] + 1e-6]])
        exact = np.array([((scores[idx] >= c) == dans[idx]).mean() for c in candidats])
        ex_aequo = np.flatnonzero(exact == exact.max())
        return float(candidats[ex_aequo[len(ex_aequo) // 2]])

    abst = np.zeros(len(scores), dtype=bool)
    for i in range(len(scores)):
        autres = np.array([j for j in range(len(scores)) if j != i])
        abst[i] = scores[i] < meilleur(autres)
    return abst, float(meilleur(np.arange(len(scores))))


def mesurer(lignes: list[dict], abst: np.ndarray) -> dict:
    out = {}
    for groupe in sorted({l["langue"] for l in lignes}) + ["global"]:
        idx = [i for i, l in enumerate(lignes) if groupe in ("global", l["langue"])]
        dans = [i for i in idx if lignes[i]["dans"]]
        hors = [i for i in idx if not lignes[i]["dans"]]
        rangs = [lignes[i]["rang"] for i in dans]
        out[groupe] = {
            "n_dans": len(dans), "n_hors": len(hors),
            "r_at_1": sum(r == 1 for r in rangs) / len(dans) if dans else None,
            "r_at_5": sum(r <= 5 for r in rangs) / len(dans) if dans else None,
            "mrr": sum(1 / r for r in rangs if r < 99) / len(dans) if dans else None,
            "abstention_a_tort": sum(bool(abst[i]) for i in dans),
            "abstention_correcte_hors": sum(bool(abst[i]) for i in hors),
            # Réponse utile : pas d'abstention et bon article en tête.
            "exactitude_bout_en_bout": sum(
                (lignes[i]["dans"] and not abst[i] and lignes[i]["rang"] == 1)
                or (not lignes[i]["dans"] and abst[i]) for i in idx) / len(idx),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/silver/rag")
    parser.add_argument("--modeles", nargs="*", default=MODELES)
    args = parser.parse_args()
    qs = questions()
    tableau, details = [], []

    for nom in args.modeles:
        moteur = Recherche(nom)
        for mode, bilingue in CONFIGS:
            if mode == "bm25" and nom != args.modeles[0]:
                continue  # BM25 ne dépend pas de l'encodeur
            lignes = []
            for q in qs:
                res, sig = moteur.rechercher(q["question"], mode, bilingue, k=50)
                labels = [r.article for r in res]
                rang = labels.index(q["reference"]) + 1 if q["reference"] in labels else 99
                score_abst = sig["bm25_max"] if mode == "bm25" else sig["cos_max"]
                lignes.append({**q, "rang": rang, "top5": labels[:5], "score_abstention": score_abst})
            scores = np.array([l["score_abstention"] for l in lignes], dtype=float)
            dans = np.array([l["dans"] for l in lignes])
            base = f"{mode}{'_bilingue' if bilingue else ''}" + ("" if mode == "bm25" else f"[{nom.split('/')[-1]}]")
            if mode == "bm25":
                # Règle Bronze figée (seuil 9,085), non réglée ici.
                variantes = [(base, scores < repondre.SEUIL_SCORE_MIN, repondre.SEUIL_SCORE_MIN)]
            else:
                abst_g, seuil_g = seuil_loo(scores, dans)
                # Seuil par écriture de la question (les cosinus n'ont pas la même échelle) :
                # arabe (ar + ar_trad), français, tunisien latin.
                groupe = np.array(["ar" if l["langue"].startswith("ar") else l["langue"] for l in lignes])
                abst_l, seuils = np.zeros(len(lignes), dtype=bool), {}
                for g in np.unique(groupe):
                    idx = np.flatnonzero(groupe == g)
                    abst_l[idx], seuils[g] = seuil_loo(scores[idx], dans[idx])
                variantes = [(base + "+seuil_global", abst_g, seuil_g),
                             (base + "+seuil_par_langue", abst_l,
                              " ".join(f"{g}:{s:.3f}" for g, s in seuils.items()))]
            for nom_cfg, abst, seuil in variantes:
                m = mesurer(lignes, abst)
                seuil_txt = round(seuil, 4) if isinstance(seuil, float) else seuil
                tableau.append({"configuration": nom_cfg, "seuil": seuil_txt, **{
                    f"{g}_{k}": v for g, d in m.items() for k, v in d.items()
                    if k in ("r_at_1", "r_at_5", "mrr", "exactitude_bout_en_bout", "abstention_a_tort",
                             "abstention_correcte_hors")}})
                details += [{"configuration": nom_cfg, "id": l["id"], "langue": l["langue"],
                             "dans": l["dans"], "reference": l["reference"], "rang": l["rang"],
                             "top5": " | ".join(l["top5"]),
                             "score_abstention": round(l["score_abstention"], 4),
                             "abstention": bool(a)} for l, a in zip(lignes, abst)]
                print(f"{nom_cfg:52s} R@1 fr={m['fr']['r_at_1']:.2f} tun={m['tun']['r_at_1']:.2f} "
                      f"ar_trad={m['ar_trad']['r_at_1']:.2f} | exactitude={m['global']['exactitude_bout_en_bout']:.3f} "
                      f"| abst. à tort={m['global']['abstention_a_tort']} hors refusées={m['global']['abstention_correcte_hors']}")
        del moteur

    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "ablations_rag.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tableau[0].keys()))
        w.writeheader()
        w.writerows(tableau)
    with open(args.sortie / "details_rag.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(details[0].keys()))
        w.writeheader()
        w.writerows(details)
    with open(args.sortie / "configuration.json", "w", encoding="utf-8") as f:
        json.dump({"jeux": [DEV.name, DEV_AR.name], "n_questions": len(qs), "modeles": args.modeles,
                   "configs": CONFIGS, "rrf_k": 60, "abstention": "seuil cosinus LOO ; BM25 : seuil Bronze",
                   "avertissement": "dev déjà consulté ; questions AR traduites automatiquement, à valider"},
                  f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
