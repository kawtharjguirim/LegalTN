"""Évalue le détecteur de divergences sur l'échantillon jugé.

Reprend les jugements (``--jugements``, JSON id -> [verdict, impact_juridique, commentaire]),
les écrit dans l'échantillon (statut ``verifie_claude`` sauf jugement humain déjà présent) et
calcule, par voie de sélection, la part de paires réellement problématiques.

Usage : python -X utf8 -m src.divergences.evaluer --jugements data/a_annoter/divergences_jugements_claude_v1.json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ECHANTILLON = RACINE / "data/a_annoter/divergences_echantillon_v1.csv"
VERDICTS = {"meme_sens", "divergence_reelle", "artefact_ocr", "artefact_segmentation"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jugements", type=Path, required=True)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/divergences")
    args = parser.parse_args()
    jugements = json.loads(args.jugements.read_text(encoding="utf-8"))
    with open(ECHANTILLON, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f))
    champs = list(lignes[0].keys()) + (["impact_juridique"] if "impact_juridique" not in lignes[0] else [])
    for l in lignes:
        if l["statut"].strip() == "verifie":       # jugement humain : on n'y touche pas
            continue
        verdict, impact, commentaire = jugements[l["id"]]
        assert verdict in VERDICTS, verdict
        l.update({"verdict": verdict, "impact_juridique": str(impact).lower(), "commentaire": commentaire,
                  "statut": "verifie_claude"})
    with open(ECHANTILLON, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)

    resultats = {"n": len(lignes), "relus_humain": sum(l["statut"] == "verifie" for l in lignes),
                 "par_selection": {}}
    for sel in ("similarite_faible", "nombres_differents", "temoin_aleatoire"):
        g = [l for l in lignes if l["selection"] == sel]
        probleme = [l for l in g if l["verdict"] != "meme_sens"]
        resultats["par_selection"][sel] = {
            "n": len(g), "verdicts": dict(Counter(l["verdict"] for l in g)),
            "part_problemes": round(len(probleme) / len(g), 3),
            "part_divergences_reelles": round(sum(l["verdict"] == "divergence_reelle" for l in g) / len(g), 3),
            "avec_impact_juridique": sum(l["impact_juridique"] == "true" for l in g),
        }
        print(f"{sel:20s} n={len(g):2d}  problèmes {len(probleme)}/{len(g)}  {dict(Counter(l['verdict'] for l in g))}")
    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "evaluation_detecteur.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
