"""Compare deux signaux d'abstention de la démo : cosinus brut (Silver) et cosinus normalisé
(question et articles sans accents / alif unifié), sur la recherche hybride e5.

Seuils par écriture, comme la démo : « fr » (questions en écriture latine, tunisien compris) et
« ar ». Mesure en leave-one-out sur le dev (77 questions, dev déjà consulté) ; le seuil retenu
pour la démo est celui réglé sur tout le dev. On applique ensuite ce seuil aux variantes
« sans accents » et « alif normalisé » pour mesurer la robustesse.

Usage : python -X utf8 -m src.audit.calibrer_signal --sortie reports/gold/abstention
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.rag.evaluer import questions, seuil_loo
from src.rag.recherche import RACINE, Recherche, repondre

from .perturbations import normalisation_alef, sans_accents

SIGNAUX = {"cosinus_brut": "cos_max", "cosinus_normalise": "cosnorm_max"}


def mesurer(dans: np.ndarray, abst: np.ndarray, rang1: np.ndarray) -> dict:
    return {
        "fausses_abstentions": int((dans & abst).sum()),
        "hors_refusees": int((~dans & abst).sum()), "n_hors": int((~dans).sum()),
        "exactitude": round(float(((dans & ~abst & rang1) | (~dans & abst)).mean()), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/abstention")
    parser.add_argument("--appareil", default="cpu")
    args = parser.parse_args()
    moteur = Recherche("intfloat/multilingual-e5-base", appareil=args.appareil)

    def interroger(q: str) -> dict:
        res, sig = moteur.rechercher(q, "hybride", False, k=3)
        return {**{nom: sig[cle] for nom, cle in SIGNAUX.items()}, "langue": sig["langue"],
                "top1": res[0].article if res else ""}

    qs = questions()
    for q in qs:
        q.update(interroger(q["question"]))
        # Variante « orthographe relâchée » : sans accents (FR), alif normalisé (AR).
        v = sans_accents(q["question"]) if q["langue"] in ("fr", "tun") else normalisation_alef(q["question"])
        q["variante"] = interroger(v) if v != q["question"] else None

    dans = np.array([q["dans"] for q in qs])
    rang1 = np.array([q["top1"] == q["reference"] for q in qs])
    groupe = np.array([q["langue"] for q in qs])
    resultats = {"n_questions": len(qs), "signaux": {}}
    for nom in SIGNAUX:
        scores = np.array([q[nom] for q in qs])
        abst_loo, seuils = np.zeros(len(qs), dtype=bool), {}
        for g in ("fr", "ar"):
            idx = np.flatnonzero(groupe == g)
            abst_loo[idx], seuils[g] = seuil_loo(scores[idx], dans[idx])
        # Robustesse : seuil de la démo (réglé sur tout le dev) appliqué aux variantes.
        var = [(i, q) for i, q in enumerate(qs) if q["variante"]]
        decision_ok = sum((q["variante"][nom] < seuils[q["langue"]]) == (q[nom] < seuils[q["langue"]])
                          for _, q in var)
        fausse_var = sum(q["dans"] and q["variante"][nom] < seuils[q["langue"]] for _, q in var)
        resultats["signaux"][nom] = {
            "seuils_demo": {g: round(s, 4) for g, s in seuils.items()},
            "leave_one_out": mesurer(dans, abst_loo, rang1),
            "variantes": {"n": len(var), "decision_identique": round(decision_ok / len(var), 3),
                          "fausses_abstentions_variante": fausse_var,
                          "dans_perimetre": sum(q["dans"] for _, q in var)},
        }
        print(f"{nom:18s} seuils {resultats['signaux'][nom]['seuils_demo']}  LOO {resultats['signaux'][nom]['leave_one_out']}"
              f"  variantes {resultats['signaux'][nom]['variantes']}")
    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "calibration_signal.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
