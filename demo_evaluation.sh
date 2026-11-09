#!/bin/bash
# Démo des scripts d'évaluation LegalTN.
# À lancer depuis la racine du projet : bash demo_evaluation.sh
# Ne lance AUCUN script de mesure sur un jeu gelé (test_locked) : chaque test ne se mesure qu'une fois par règle.
set -e
cd "$(dirname "$0")"

echo "== 1. Démo : question en formulation juridique complète =="
python3 -I src/demo/repondre.py "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"

echo
echo "== 2. Démo : question hors périmètre (doit s'abstenir) =="
python3 -I src/demo/repondre.py "Quelle est la capitale de la Tunisie ?"

echo
echo "== 3. Démo : question avec sigle (CDI développé par le lexique de sigles) =="
python3 -I src/demo/repondre.py "Quel est le délai de préavis pour rompre un CDI ?"


# Étapes 4 et 5 désactivées : les scripts analyse_erreurs_bout_en_bout.py et
# analyse_erreurs_ocr.py n'ont pas été récupérés (absents du dépôt). Avec set -e,
# leur appel arrêtait le script. À réactiver s'ils sont retrouvés.
# echo
# echo "== 4. Analyse des erreurs de la démo sur le dev v5 (lecture seule) =="
# python3 -I src/evaluation/analyse_erreurs_bout_en_bout.py
#
# echo
# echo "== 5. Analyse des erreurs corrigées dans le texte OCR (lecture seule) =="
# python3 -I src/evaluation/analyse_erreurs_ocr.py
