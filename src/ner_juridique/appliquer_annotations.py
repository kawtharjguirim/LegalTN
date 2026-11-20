"""Applique un fichier d'annotations textuelles (entité, type, occurrence) aux lots NER.

Calcule les positions de caractères, refuse toute entité introuvable ou chevauchante, signale
les bornes qui coupent un mot, sauvegarde le lot d'origine dans ``data/a_annoter/sauvegardes/``
puis écrit le lot avec le statut donné (``verifie_claude`` par défaut : annotation par Claude, à
relire ; seul ``verifie`` signifie relu par un humain).

Usage : python -X utf8 -m src.ner_juridique.appliquer_annotations data/a_annoter/annotations_claude_dev_v1.json
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

from .regles import TYPES, lisible, vers_texte

RACINE = Path(__file__).resolve().parents[2]
LOTS = {"fr": RACINE / "data/a_annoter/ner_dev_fr_v1.csv", "ar": RACINE / "data/a_annoter/ner_dev_ar_v1.csv"}


def positions(phrase: str, annotations: list) -> tuple[list, list[str]]:
    entites, alertes = [], []
    for texte, type_, occ in annotations:
        if type_ not in TYPES:
            raise ValueError(f"type inconnu {type_!r}")
        debut = -1
        for _ in range(occ + 1):
            debut = phrase.find(texte, debut + 1)
            if debut < 0:
                raise ValueError(f"introuvable (occurrence {occ}) : {texte!r}")
        fin = debut + len(texte)
        if (debut > 0 and phrase[debut - 1].isalnum()) or (fin < len(phrase) and phrase[fin].isalnum()):
            alertes.append(f"borne au milieu d'un mot : {texte!r}")
        entites.append((debut, fin, type_))
    entites.sort()
    for a, b in zip(entites, entites[1:]):
        if a[1] > b[0]:
            raise ValueError(f"chevauchement : {phrase[a[0]:a[1]]!r} / {phrase[b[0]:b[1]]!r}")
    return entites, alertes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--statut", default="verifie_claude")
    parser.add_argument("--commentaire", default="annoté par Claude (annotations_claude_dev_v1.json), à relire")
    args = parser.parse_args()
    donnees = json.loads(args.annotations.read_text(encoding="utf-8"))

    sauvegardes = RACINE / "data/a_annoter/sauvegardes"
    sauvegardes.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    for langue, chemin in LOTS.items():
        if langue not in donnees:
            continue
        lignes = list(csv.DictReader(open(chemin, encoding="utf-8-sig", newline="")))
        champs = list(lignes[0].keys())
        manquants = {l["item_id"] for l in lignes} - set(donnees[langue])
        if manquants:
            raise SystemExit(f"{langue} : phrases sans annotation : {sorted(manquants)}")
        humaines = [l["item_id"] for l in lignes if l["statut"].strip() == "verifie"]
        if humaines:
            raise SystemExit(f"{langue} : {len(humaines)} phrases déjà relues par un humain ; rien écrasé.")
        shutil.copy2(chemin, sauvegardes / f"{chemin.stem}_avant_{horodatage}.csv")
        n_ent, changees, alertes = 0, 0, []
        for l in lignes:
            entites, a = positions(l["phrase"], donnees[langue][l["item_id"]])
            alertes += [f"{l['item_id']} : {x}" for x in a]
            nouveau = vers_texte(entites)
            changees += nouveau != l["entites"]
            l["entites"], l["entites_lisibles"] = nouveau, lisible(l["phrase"], entites)
            l["statut"], l["commentaire"] = args.statut, args.commentaire
            n_ent += len(entites)
        with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=champs)
            w.writeheader()
            w.writerows(lignes)
        print(f"{langue} : {len(lignes)} phrases, {n_ent} entités, {changees} phrases modifiées "
              f"par rapport aux règles -> {chemin.name} (sauvegarde dans {sauvegardes.name}/)")
        for a in alertes:
            print("  alerte", a)


if __name__ == "__main__":
    main()
