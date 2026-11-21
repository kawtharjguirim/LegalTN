"""Prépare le dossier publiable ``data/publication/legaltn_v1/`` (sans texte intégral des articles).

Contenu :
- ``alignement_fr_ar_v1.csv`` : paires d'articles AR/FR (numéros, pages, statut, similarité LaBSE,
  écart de nombres), SANS le texte des articles ;
- ``obligations_dev_v1.csv`` (+ ``obligations_test_v1.csv`` avec ``--avec-test``, seulement après la
  mesure finale du test, qui ne se fait qu'une fois) : annotations qui / modal / quoi / quand,
  sans la colonne ``phrase`` (remplacée par son empreinte SHA-256, pour relier la ligne à la source) ;
- ``questions_dev_v1.csv`` : questions de développement FR/AR/tunisien (rédigées pour le projet) ;
- ``CHECKSUMS.sha256``.
Les fiches (``README.md``, ``FICHE_DONNEES.md``, ``LICENCE.md``) sont écrites à la main et conservées.

Variante ``--avec-phrases`` : garde la colonne ``phrase`` (à n'utiliser qu'une fois la licence de
l'édition source clarifiée). Les jeux ``data/test_locked`` ne sont jamais copiés tels quels.

Usage : python -X utf8 -m src.publication.preparer [--avec-phrases]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "data/publication/legaltn_v1"


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ecrire(chemin: Path, champs: list[str], lignes: list[dict]) -> None:
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, lineterminator="\n")
        w.writeheader()
        w.writerows(lignes)


def sha(texte: str) -> str:
    return hashlib.sha256(" ".join(texte.split()).encode("utf-8")).hexdigest()[:16]


def alignement() -> int:
    scores = {(s["article_ar"], s["article_fr"]): s for s in lire(RACINE / "reports/gold/divergences/paires_scores.csv")}
    lignes = []
    for a in lire(RACINE / "data/processed/alignement_fr_ar_v6.csv"):
        s = scores.get((a["article_ar"], a["article_fr"]), {})
        lignes.append({"article_ar": a["article_ar"], "page_ar": a["page_ar"], "article_fr": a["article_fr"],
                       "page_fr": a["page_fr"], "statut": a["statut"], "abroge": a["abroge"],
                       "similarite_labse": s.get("similarite", ""), "ecart_nombres": s.get("ecart_nombres", "")})
    ecrire(SORTIE / "alignement_fr_ar_v1.csv", list(lignes[0]), lignes)
    return len(lignes)


def obligations(avec_phrases: bool, avec_test: bool) -> dict[str, int]:
    n = {}
    for lot in (("dev", "test") if avec_test else ("dev",)):
        champs = ["obligation_id", "article_fr", "page_fr", "phrase_sha256", "qui", "modal", "quoi", "quand", "commentaire", "statut"]
        if avec_phrases:
            champs.insert(3, "phrase")
        lignes = []
        for l in lire(RACINE / f"data/a_annoter/obligations_{lot}_claude_v1.csv"):
            l["phrase_sha256"] = sha(l["phrase"])
            lignes.append({c: l.get(c, "") for c in champs})
        ecrire(SORTIE / f"obligations_{lot}_v1.csv", champs, lignes)
        n[lot] = len(lignes)
    return n


def questions() -> int:
    champs = ["id", "langue", "type", "question", "article_reference", "statut"]
    lignes = []
    for l in lire(RACINE / "data/dev/questions_dev_v2.csv"):
        lignes.append({"id": l["id"], "langue": l["langue"], "type": l["type"], "question": l["question"],
                       "article_reference": l["article_reference"], "statut": "verifie"})
    for nom, source in (("AR", "questions_dev_ar_traduites_v1.csv"), ("TUN", "questions_tun_v1.csv")):
        for l in lire(RACINE / "data/dev" / source):
            lignes.append({"id": l["id"], "langue": l["langue"], "type": l.get("type", "dans_perimetre"),
                           "question": l["question"], "article_reference": l["article_reference"],
                           "statut": l["statut"]})
    ecrire(SORTIE / "questions_dev_v1.csv", champs, lignes)
    return len(lignes)


def sommes() -> None:
    fichiers = sorted(p for p in SORTIE.iterdir() if p.is_file() and p.name != "CHECKSUMS.sha256")
    with open(SORTIE / "CHECKSUMS.sha256", "w", encoding="utf-8", newline="") as f:
        for p in fichiers:
            f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()} *{p.name}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--avec-phrases", action="store_true")
    parser.add_argument("--avec-test", action="store_true",
                        help="Inclure les annotations du test (seulement après la mesure finale, unique).")
    args = parser.parse_args()
    SORTIE.mkdir(parents=True, exist_ok=True)
    print("alignement :", alignement(), "lignes")
    print("obligations :", obligations(args.avec_phrases, args.avec_test))
    print("questions :", questions(), "lignes")
    sommes()
    print("->", SORTIE)


if __name__ == "__main__":
    main()
