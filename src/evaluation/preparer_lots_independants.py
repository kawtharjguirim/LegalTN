"""Préparation des lots d'annotation humaine indépendants du dev.

Reconstruction du script Codex refusé (ajout ~80 lignes), à partir des
specifications consignées dans experiments.md / obligations_guide :

- ``obligations_candidats_test_v1.csv`` : 100 phrases à marqueur tirées du
  corpus FR corrigé, disjointes des 200 candidates dev, graine 20261101,
  champs d'annotation **vides** (jamais pré-remplis).
- ``rappel_alignement_a_annoter_v1.csv`` : 60 articles arabes hors dev
  v1/v2, graine 20261030, pour mesurer le rappel d'alignement.
- ``ner_a_annoter_v1.csv`` : phrases pour annotation NER, champ ``entites``
  vide au format ``debut|fin|TYPE;...`` prévu par le guide NER.

Ce script prépare des lots ; il ne produit aucune annotation ni métrique.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import unicodedata
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.obligation_extraction.extraire_obligations import trouver_modal

RACINE = Path(__file__).resolve().parents[2]
GRAINE_TEST = 20261101
GRAINE_RAPPEL = 20261030
GRAINE_NER = 20261102
N_TEST = 100
N_RAPPEL = 60
N_NER = 60

RE_PHRASE = re.compile(r"(?<=[.!?])\s+")


def _norm(t: str) -> str:
    return " ".join(unicodedata.normalize("NFC", t).split()).lower()


def _lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def phrases_dev() -> set:
    return {_norm(r["phrase"]) for r in _lire(
        RACINE / "data/dev/obligations_candidats_dev_v1.csv")}


def preparer_lot_obligations_test(sortie: Path) -> int:
    """Tire N_TEST phrases à marqueur hors dev, graine fixe, champs vides."""
    dev = phrases_dev()
    articles = _lire(RACINE / "data/processed/articles_fr_corrige.csv")
    candidats = []
    for a in articles:
        for ph in RE_PHRASE.split(a["texte_fr"]):
            ph = ph.strip()
            if len(ph) < 25 or _norm(ph) in dev:
                continue
            modal, _ = trouver_modal(ph)
            if modal:
                candidats.append({"article_fr": a["article_id"],
                                  "page_fr": a["page"], "phrase": ph})
    vus, uniques = set(), []
    for c in candidats:
        if _norm(c["phrase"]) not in vus:
            vus.add(_norm(c["phrase"]))
            uniques.append(c)
    rng = random.Random(GRAINE_TEST)
    tires = rng.sample(uniques, min(N_TEST, len(uniques)))
    sortie.parent.mkdir(parents=True, exist_ok=True)
    champs = ["obligation_id", "article_fr", "page_fr", "phrase",
              "qui", "modal", "quoi", "quand", "commentaire"]
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for i, c in enumerate(tires, 1):
            w.writerow({"obligation_id": f"T{i:03d}", **c,
                        "qui": "", "modal": "", "quoi": "",
                        "quand": "", "commentaire": ""})
    print(f"lot test obligations : {len(tires)}/{len(uniques)} -> {sortie}")
    return len(tires)


def preparer_lot_rappel(sortie: Path) -> int:
    """60 articles AR hors dev v1/v2 pour l'estimation du rappel."""
    exclus = set()
    for nom in ("alignement_dev_v1.csv", "alignement_dev_v2_a_annoter.csv"):
        exclus |= {r["article_ar"] for r in _lire(RACINE / "data/dev" / nom)}
    articles = [a for a in _lire(RACINE / "data/processed/articles_ar.csv")
                if a["article_id"] not in exclus]
    rng = random.Random(GRAINE_RAPPEL)
    tires = rng.sample(articles, min(N_RAPPEL, len(articles)))
    tires.sort(key=lambda a: int(a["page"]))
    champs = ["item_id", "article_ar", "numero_ar", "page_ar",
              "debut_texte_ar", "article_fr_attendu", "verdict_image",
              "commentaire"]
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for i, a in enumerate(tires, 1):
            w.writerow({"item_id": f"R{i:03d}", "article_ar": a["article_id"],
                        "numero_ar": a["numero"], "page_ar": a["page"],
                        "debut_texte_ar": a["texte_ar"][:120],
                        "article_fr_attendu": "", "verdict_image": "",
                        "commentaire": ""})
    print(f"lot rappel alignement : {len(tires)} -> {sortie}")
    return len(tires)


def preparer_lot_ner(sortie: Path) -> int:
    """Phrases FR pour annotation NER (entités rôles/institutions/délais)."""
    articles = _lire(RACINE / "data/processed/articles_fr_corrige.csv")
    phrases = []
    for a in articles:
        for ph in RE_PHRASE.split(a["texte_fr"]):
            ph = ph.strip()
            if 40 <= len(ph) <= 300:
                phrases.append({"article_fr": a["article_id"],
                                "page_fr": a["page"], "phrase": ph})
    rng = random.Random(GRAINE_NER)
    tires = rng.sample(phrases, min(N_NER, len(phrases)))
    champs = ["item_id", "article_fr", "page_fr", "phrase", "entites",
              "commentaire"]
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for i, c in enumerate(tires, 1):
            w.writerow({"item_id": f"N{i:03d}", **c,
                        "entites": "", "commentaire": ""})
    print(f"lot NER : {len(tires)} -> {sortie}")
    return len(tires)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seulement", choices=["obligations", "rappel", "ner"],
                        default=None)
    args = parser.parse_args(argv)
    if args.seulement in (None, "obligations"):
        preparer_lot_obligations_test(
            RACINE / "data/test_locked/obligations_candidats_test_v1.csv")
    if args.seulement in (None, "rappel"):
        preparer_lot_rappel(
            RACINE / "data/dev/rappel_alignement_a_annoter_v1.csv")
    if args.seulement in (None, "ner"):
        preparer_lot_ner(RACINE / "data/dev/ner_a_annoter_v1.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
