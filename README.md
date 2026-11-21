# LegalTN

Projet NLP sur le Code du travail tunisien en arabe et français.
Cette copie est en cours de récupération. L'alignement, la démonstration BM25
et un adaptateur HTTP local fonctionnent. Les corpus AR/FR, le PDF source et les
caches OCR sont disponibles. Trois fichiers gelés ont été récupérés et la suite
de tests actuelle passe. Une partie des références d'évaluation et plusieurs
composants du projet complet restent à récupérer.

L'état vérifié et les exigences Bronze sont consignés dans
[`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md). Les résultats de
[`experiments.md`](experiments.md) sont historiques ; ils ne constituent pas des
résultats tous reproduits sur cette copie. Les entrées de reprise distinguent
les exécutions actuelles des résultats hérités.

## Démonstration et API locale

La démonstration récupérée utilise uniquement la bibliothèque standard Python :

```powershell
python -X utf8 src/demo/repondre.py "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"
```

Elle retourne un extrait cité, pas une consultation juridique rédigée.
Les scripts `src/demo/repondre.py` et `src/evaluation/baseline_bm25.py` sont
conservés à l'identique. Le seuil historique reste à 9,085.

L'adaptateur `api.py` et le lanceur ci-dessous ont été ajoutés pendant la reprise ;
ils ne proviennent pas de l'API Codex manquante :

```powershell
.\demarrer.ps1 -Port 18765
```

Alternative : `python -X utf8 api.py --port 18765`.
Le serveur écoute uniquement sur `127.0.0.1`. Dans un autre terminal :

```powershell
Invoke-RestMethod http://127.0.0.1:18765/health
$corps = @{question = "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"; k = 1} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:18765/repondre -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($corps))
```

`POST /repondre` renvoie la langue, l'abstention éventuelle, les articles/pages/
extraits candidats et la latence. `k` est optionnel (3 par défaut, entre 1 et 5).
Le lancement PowerShell et les requêtes FR/AR/hors périmètre ont été vérifiés ;
les serveurs de vérification ont ensuite été arrêtés.

Limites observées : le sigle « CDI » déclenche une abstention à tort ; les
intitulés BM25 gèrent moins de suffixes que l'alignement et peuvent fusionner
des sous-articles. Ce comportement historique est documenté, pas corrigé
silencieusement au prix d'une modification des expériences de référence.

## Contrôle sur développement et tableaux

```powershell
python src/evaluation/evaluer_dev_reprise.py --rapports reports/mon_controle_dev
```

Choisir un dossier neuf. Le script compare le seuil historique à la même
récupération sans seuil de score, sans réglage et sans lire de jeu de test.
Les références sont celles du dev v2 déjà utilisé historiquement.

Rapports générés dans `reports/reprise/demo_dev/` :

- `evaluation_demo_dev_v2.json` : configuration, empreintes et résultats détaillés ;
- `tableau1_demo_dev.csv` : comparaison globale sur développement ;
- `tableau2_langues_dev.csv` : résultats par langue ;
- `tableau3_erreurs_dev.csv` et `erreurs_dev.csv` : catégories automatiques et exemples.

Sur ce dev de 56 questions : 35 erreurs sans seuil contre 8 avec le seuil
historique ; 27 erreurs évitées selon le critère « hors périmètre accepté,
abstention à tort ou premier article incorrect ». Cela comprend néanmoins
4 fausses abstentions, et le rappel article@5 passe de 23/27 à 21/27.
Les questions arabes de ce dev sont toutes hors périmètre : aucun rappel de
recherche en arabe n'y est mesurable. Ces tableaux **ne sont pas les résultats
finaux sur test indépendant** et ne confirment pas les chiffres de la session Codex.

## Lancer l'alignement

Depuis le dossier du projet (environnement vérifié : Python 3.12.2) :

```powershell
python -m pip install -r requirements-alignement.txt
python src/executer_alignement.py --sortie reports/mon_alignement
```

Choisir un dossier de sortie neuf : si l'un des trois exports v6 existe, le
programme refuse de l'écraser. Les fichiers d'entrée restent dans
`data/processed/`, indépendamment du dossier de sortie.

Les résultats de la reprise sont déjà disponibles sous
`data/processed/alignement_fr_ar_v6.csv`, `alignement_resume_v6.json` et
`alignement_echantillon_image_v6.csv`. Une seconde exécution dans
`reports/reprise/reproduction_v6/` a produit les mêmes fichiers octet par octet.

Résultat actuel : 515 entrées AR, 498 entrées FR, 494 appariements,
21 lignes classées `abrogé (plage)`, 4 hors Code et 6 contrôles d'années.
Ces comptes décrivent la sortie du pipeline ; ils ne constituent pas une
précision ou un rappel sur une référence indépendante.

## Contrôler les fichiers récupérés

Depuis le dossier du projet, avec Python 3.11 ou ultérieur :

```powershell
python src/auditer_reprise.py
```

Ce contrôle utilise uniquement la bibliothèque standard. Il lit les données,
compare leurs empreintes, contrôle les références françaises et la syntaxe du
notebook 01, puis affiche un rapport JSON. Il exécute uniquement les définitions
de normalisation auditées du notebook d'alignement v5 pour contrôler les références
de développement. Aucun fichier n'est modifié et aucun notebook n'est exécuté
intégralement ; aucun score de test indépendant n'est mesuré.

Le rapport obtenu pendant la récupération est disponible dans
[`reports/reprise/audit_donnees_recuperees.json`](reports/reprise/audit_donnees_recuperees.json).
Le contrôle étendu après récupération des notebooks d'alignement est dans
[`reports/reprise/audit_alignement_v5.json`](reports/reprise/audit_alignement_v5.json).
Le rapport actuel après récupération du corpus arabe et exécution complète est
[`reports/reprise/audit_alignement_complet.json`](reports/reprise/audit_alignement_complet.json).
Une sortie réussie du script indique que les contrôles ont pu être effectués ;
les anomalies sont détaillées dans le rapport.

## Éléments récupérés

- `data/processed/texte_travail.json` : texte de travail de 291 pages.
- `data/processed/articles_ar.csv` : 515 entrées arabes segmentées.
- `data/processed/articles_fr.csv` et `articles_fr_corrige.csv` : deux versions
  de 498 entrées ; les identifiants FR ne sont pas uniques.
- `data/dev/questions_dev_v2.csv` : 56 questions de développement, déjà utilisées
  historiquement pour la calibration.
- `notebooks/01_data_exploration.ipynb` : exploration/OCR, conservée avec ses
  sorties historiques.
- `notebooks/03_alignement_fr_ar.ipynb`, `03_alignement_fr_ar_v4.ipynb` et
  `03_alignement_fr_ar_v5.ipynb` : versions originales d'alignement conservées
  à l'identique. La v5 est celle documentée par le pipeline historique.
- `docs/Guide_Revue_Bronze.pdf` : guide de présentation, distinct du cahier des
  charges complet de LegalTN.
- `data/raw/arabic/majallat_al_shughl_2019.pdf` : PDF source de 291 pages,
  empreinte identique à celle du journal historique.
- `data/processed/page_images/`, `ocr_pages/`, `ocr_pages_fr/`, `ocr_bandes/` :
  images et caches hérités, conservés sans recalcul.
- Tables de notes, corrections et vérifications, ainsi que les anciens exports
  d'alignement : sources récupérées, non modifiées.
- `src/evaluation/baseline_bm25.py` et `src/demo/repondre.py` :
  baseline et démonstration récupérées à l'identique.
- `data/test_locked/questions_reference_v2.csv`, `ocr_candidats_v1.csv` et
  `ocr_baseline_v1.csv` : fichiers gelés récupérés, empreintes historiques vérifiées.

Les CSV de développement d'alignement et les candidats d'obligations présents
avant cette récupération sont conservés. Les champs d'annotation des obligations
restent vides.

## Démarrage et tests applicatifs

Les règles d'alignement récupérées ont maintenant une suite ciblée :

```powershell
python -m unittest discover -s tests -p test_alignement_notebook.py -v
```

Elle utilise pandas (version vérifiée : 2.2.2 ; les notebooks utilisent
`include_groups=False`, disponible à partir de pandas 2.2). **10 tests exécutés
et réussis**, avec des fixtures synthétiques et des exports temporaires.
Ces tests ne remplacent pas une évaluation sur le corpus complet.

La commande complète est `python -m pytest`. Dépendances de vérification :
`python -m pip install -r requirements-alignement.txt pytest==9.2.0`.
La dernière exécution donne **21 tests réussis et 1 échec attendu (`xfail`)**,
avec un code de sortie 0. Le contrôle des empreintes passe après récupération
des trois fichiers gelés ; aucun test n'a été désactivé. Le xfail strict documente
la fausse abstention sur « CDI ». Les « 36 tests réussis » Codex ne sont pas confirmés :
la suite actuellement disponible comporte 22 tests, dont les ajouts de la reprise.

`demo_evaluation.sh` peut lancer les questions de démonstration, mais ses deux
scripts d'analyse historiques restent absents. Les tests logiciels ne relancent
aucune mesure sur les jeux gelés. Leur récupération ne réinitialise pas le gel :
les évaluations historiques de questions v2 restent déjà consommées ; ne pas
utiliser `--evaluer` ou la baseline en mode mesure pour régler le système.

Le notebook 01 n'a pas besoin d'être relancé pour utiliser les données récupérées :
il peut réécrire `texte_travail.json`. Tesseract est installé localement, mais les
langues `ara` et `fra` restent absentes pour refaire l'OCR. Les notebooks
de segmentation et de correction française sont encore à récupérer ;
le notebook 01 ne remplace pas leurs traitements.

## Version de travail de l'alignement

`notebooks/03_alignement_fr_ar_v6.ipynb` conserve les règles de calcul v5 et corrige
deux problèmes opérationnels : repérage de la racine sans `data/raw/` et refus
d'écraser les sorties existantes, notamment l'échantillon pouvant être annoté.
Les sorties portent le suffixe `_v6` ; les fichiers historiques sont préservés.

Cette version a été exécutée sur les corpus réels et testée sur fixtures.
Les sources récupérées restent inchangées. Le rapport décrit notamment
69 étiquettes FR sans suffixe, 17 appariements dont le drapeau AR indique
`abroge=True`, et la longueur stockée incohérente d'AR-367.
L'indépendance des jeux, les métriques finales et la validité des corrections
juridiques ne sont pas établies par ces contrôles techniques.
