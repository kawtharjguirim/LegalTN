"""Écrit les annotations d'obligations (JSON) dans des CSV au format du modèle.

Entrée : ``data/a_annoter/obligations_claude_v1.json`` (id -> [modal, qui, quoi, quand, commentaire]).
Sorties : ``data/a_annoter/obligations_dev_claude_v1.csv`` et ``obligations_test_claude_v1.csv``,
colonnes du modèle + ``statut`` (``verifie_claude`` ; ``verifie`` seulement après relecture humaine).

Le fichier gelé ``data/test_locked/obligations_candidats_test_v1.csv`` n'est jamais modifié : le test
annoté est écrit à part. Refuse d'écraser un CSV dont des lignes sont déjà relues (``verifie``).

Usage : python -X utf8 -m src.obligation_extraction.appliquer_annotations
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ANNOTATIONS = RACINE / "data/a_annoter/obligations_claude_v1.json"
LOTS = {
    "dev": (RACINE / "data/dev/obligations_candidats_dev_v1.csv", RACINE / "data/a_annoter/obligations_dev_claude_v1.csv"),
    "test": (RACINE / "data/test_locked/obligations_candidats_test_v1.csv", RACINE / "data/a_annoter/obligations_test_claude_v1.csv"),
}
CHAMPS = ["obligation_id", "article_fr", "page_fr", "phrase", "qui", "modal", "quoi", "quand", "commentaire", "statut"]


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def appliquer() -> None:
    annotations = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))["annotations"]
    for nom, (source, sortie) in LOTS.items():
        if sortie.exists() and any(l.get("statut") == "verifie" for l in lire(sortie)):
            print(f"{sortie.name} : des lignes sont relues par un humain, rien réécrit.")
            continue
        lignes = []
        for l in lire(source):
            modal, qui, quoi, quand, commentaire = annotations[l["obligation_id"]]
            lignes.append({**{k: l[k] for k in ("obligation_id", "article_fr", "page_fr", "phrase")},
                           "qui": qui, "modal": modal, "quoi": quoi, "quand": quand,
                           "commentaire": commentaire, "statut": "verifie_claude"})
        with open(sortie, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CHAMPS)
            w.writeheader()
            w.writerows(lignes)
        n_non = sum(1 for l in lignes if not l["modal"])
        print(f"{nom} : {len(lignes)} lignes ({len(lignes) - n_non} obligations, {n_non} non retenues) -> {sortie.name}")


if __name__ == "__main__":
    appliquer()
