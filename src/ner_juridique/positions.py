"""Aide à l'annotation : positions de caractères d'un texte dans une phrase.

Usage : python -X utf8 -m src.ner_juridique.positions "phrase complète" "entité" [TYPE]
Affiche chaque occurrence au format du guide (debut|fin|TYPE).
"""

import sys


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        return
    phrase, cible = sys.argv[1], sys.argv[2]
    type_ = sys.argv[3] if len(sys.argv) > 3 else "TYPE"
    debut, trouve = 0, False
    while (pos := phrase.find(cible, debut)) >= 0:
        print(f"{pos}|{pos + len(cible)}|{type_}")
        trouve, debut = True, pos + 1
    if not trouve:
        print("Introuvable : vérifier espaces et apostrophes (’ ou ').")


if __name__ == "__main__":
    main()
