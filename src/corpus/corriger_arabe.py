"""Applique les corrections vérifiées du texte arabe numérisé : ``corrections_ar.csv`` -> ``articles_ar_corrige.csv``.

Le fichier d'origine ``articles_ar.csv`` n'est jamais modifié (son empreinte est contrôlée par les tests de reprise).
Chaque correction remplace une chaîne ``avant`` qui doit apparaître **exactement une fois** dans l'article ; sinon la
commande échoue (pas de correction approximative). Colonne ``verification`` : ``image`` (lu sur l'image de la page du
PDF) ou ``francais`` (déduit du texte français de l'article équivalent, à confirmer sur image).

Usage : python -X utf8 -m src.corpus.corriger_arabe
"""

from __future__ import annotations

import csv
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ORIGINE = RACINE / "data/processed/articles_ar.csv"
CORRECTIONS = RACINE / "data/processed/corrections_ar.csv"
SORTIE = RACINE / "data/processed/articles_ar_corrige.csv"


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def appliquer(origine: Path = ORIGINE, corrections: Path = CORRECTIONS, sortie: Path = SORTIE) -> dict:
    lignes = lire(origine)
    par_id = {l["article_id"]: l for l in lignes}
    bilan = {"corrections": 0, "image": 0, "francais": 0, "articles": set()}
    for c in lire(corrections):
        ligne = par_id[c["article_ar"]]
        n = ligne["texte_ar"].count(c["avant"])
        if n != 1:
            raise SystemExit(f'{c["article_ar"]} : « {c["avant"]} » trouvé {n} fois (attendu : 1)')
        ligne["texte_ar"] = ligne["texte_ar"].replace(c["avant"], c["apres"])
        ligne["corrections"] = (ligne.get("corrections", "") + f' ; vérifié {c["verification"]} : {c["justification"]}').lstrip(" ;")
        ligne["longueur"] = str(len(ligne["texte_ar"]))
        bilan["corrections"] += 1
        bilan[c["verification"]] += 1
        bilan["articles"].add(c["article_ar"])
    with open(sortie, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    bilan["articles"] = len(bilan["articles"])
    return bilan


def main() -> None:
    b = appliquer()
    print(f'{b["corrections"]} corrections sur {b["articles"]} articles ({b["image"]} lues sur image, {b["francais"]} déduites du français) -> {SORTIE.name}')


if __name__ == "__main__":
    main()
