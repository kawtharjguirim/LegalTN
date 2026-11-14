# Installation de LegalTN

Ce document liste ce qu'il faut installer pour faire tourner LegalTN, du plus simple
(la démo) au plus complet (tests, NER CRF, notebooks OCR).

Les commandes marquées **vérifié** ont été exécutées le 14/11/2026 sur Windows 10,
dans un environnement Python vierge (Python 3.11.9). Le projet a aussi été utilisé
avec Python 3.12.2.

## 1. Prérequis

| Outil | Version | Pour quoi faire |
|---|---|---|
| Python | 3.11 ou 3.12 | tout le projet |
| Git | récent | récupérer le dépôt |
| Tesseract OCR (langues `ara` et `fra`) | — | uniquement pour relancer l'OCR des notebooks |

## 2. Récupérer le projet

```powershell
git clone https://github.com/kawtharjguirim/LegalTN
cd LegalTN
```

## 3. Créer un environnement Python

**Ne pas utiliser le dossier `.venv` présent dans le dépôt.** Il a été créé sur un autre
poste et pointe vers `C:\Python312\python.exe` : sur une autre machine, il échoue avec
l'erreur `No Python at 'C:\Python312\python.exe'`. Le script `demarrer.ps1` l'utilise en
priorité, donc il échoue aussi tant que ce dossier est dans le dépôt (voir section 8).

Créez votre propre environnement **en dehors du dossier du projet**, pour ne pas le
mélanger aux fichiers suivis par git :

```powershell
python -m venv $HOME\venvs\legaltn
$py = "$HOME\venvs\legaltn\Scripts\python.exe"
& $py --version
```

Dans la suite, `$py` désigne ce Python. Si vous ouvrez un nouveau terminal, redéfinissez
la variable `$py` avec la deuxième ligne ci-dessus.

## 4. Niveau 1 — Démo et interface web (aucun paquet à installer)

La démo, la recherche BM25, la règle d'abstention et l'API utilisent uniquement la
bibliothèque standard de Python.

Démo en ligne de commande (**vérifié**) :

```powershell
& $py -X utf8 src/demo/repondre.py "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"
```

Résultat attendu : l'article 14 bis (page PDF 279) en premier.

API et interface web (**vérifié**) :

```powershell
& $py -X utf8 api.py --port 8000
```

Puis ouvrir http://127.0.0.1:8000 dans un navigateur. Points d'accès :
- `GET /health` : renvoie le nombre d'articles indexés (496 FR, 491 AR) ;
- `POST /repondre` avec `{"question": "...", "k": 3}`.

Arrêter le serveur avec `Ctrl+C`.

## 5. Niveau 2 — Tests, alignement et NER CRF

```powershell
& $py -m pip install -r requirements-alignement.txt pytest sklearn-crfsuite nltk
```

Versions installées lors de la vérification : numpy 2.4.1, pandas 2.2.2, pytest 9.2.0,
sklearn-crfsuite 0.5.0 (avec python-crfsuite 0.9.12 et scikit-learn 1.9.1), nltk 3.10.4.

Lancer les tests (**vérifié** : 47 réussis, 1 xfail attendu sur le sigle « CDI », 0 échec) :

```powershell
& $py -m pytest -q -p no:cacheprovider
```

Les tests ne lancent aucune mesure sur `data/test_locked/` : ils vérifient seulement les
empreintes SHA-256 des jeux gelés et le code.

Reproduction de la baseline CoNLL-2002 (**vérifié** : F1 35,95 contre 35,86 publié). Le
script télécharge le corpus `conll2002` de NLTK au premier lancement (connexion Internet
nécessaire) :

```powershell
& $py -X utf8 src/ner_crf/reproduire_baseline_conll.py
```

Attention : sans l'option `--sortie`, le script réécrit
`reports/reprise/conll2002_reproduction.json`.

## 6. Niveau 3 — Supports de la revue (non vérifié)

`src/rapports/generer_supports_bronze.py` importe `matplotlib` et `Pillow` :

```powershell
& $py -m pip install matplotlib pillow
```

Ce script n'a pas été relancé lors de la vérification.

## 7. Niveau 4 — Notebooks OCR et segmentation (non vérifié)

Les notebooks de `notebooks/` utilisent PyMuPDF, Pillow, pandas, numpy, matplotlib et
Tesseract (langues `ara+fra`, chemin réglé par la variable `TESSERACT_CMD` dans les
notebooks) :

```powershell
& $py -m pip install pymupdf pillow pandas numpy matplotlib jupyter
```

Tesseract n'est pas un paquet Python : il s'installe à part, avec les données de langue
arabe et française. Ces notebooks n'ont pas été relancés lors de la vérification ; les
relancer peut réécrire des fichiers de `data/processed/`.

## 8. Problèmes connus

- **Le dossier `.venv` est suivi par git** (environ 13 600 fichiers) et ne fonctionne que
  sur le poste où il a été créé. Il faudrait le retirer du dépôt (`git rm -r --cached .venv`)
  et ajouter un fichier `.gitignore` contenant `.venv/`. À faire avec l'accord de toute
  l'équipe, car cela touche le dépôt partagé.
- **Accents dans le terminal** : lancer Python avec `-X utf8` (comme dans les commandes
  ci-dessus) évite les caractères mal affichés sous Windows.
