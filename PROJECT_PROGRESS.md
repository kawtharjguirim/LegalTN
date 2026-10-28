# LegalTN — état vérifié et reprise

Audit du 27 octobre 2026, dans `C:\Users\Moham\Downloads\LegalTN`.

## Étape 7 — fichiers gelés récupérés, suite de tests sans échec inattendu

Les trois fichiers fournis depuis `Downloads` ont été vérifiés avant copie
puis intégrés dans `data/test_locked/`, sans modification. Leur contenu
correspond exactement aux empreintes de `tests/test_evaluation.py` et du journal.

| Fichier | Lignes de données | SHA-256 |
|---|---:|---|
| `questions_reference_v2.csv` | 40 | `0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083` |
| `ocr_candidats_v1.csv` | 30 | `0969c1aa98193fb40c1c8d9989f3fa4599ec072f4e9eab3448b5d0a7fc927608` |
| `ocr_baseline_v1.csv` | 30 | `f2be31a94d64886b313ec5a41f1d9dbcfc396d8a42126c1585417f2301cb59d3` |

Aucune ligne CSV mal formée détectée. Provenance et empreintes consignées dans
`reports/reprise/recuperation_jeux_geles.json`.

**Tests réellement exécutés :**

```text
python -m pytest -q -p no:cacheprovider
21 passed, 1 xfailed, 17 subtests passed in 2.60s
```

Code de sortie **0**, avec Python 3.12.2 et pytest 9.2.0 (installation temporaire
réutilisée via `PYTHONPATH`, sans installation globale). La suite comporte
10 tests d'alignement, 5 tests HTTP et les 7 tests historiques : 6 réussites
historiques et 1 xfail strict sur le sigle « CDI ». Les sous-tests ne sont pas
des tests indépendants supplémentaires.

Le dernier échec inattendu est résolu par la récupération des données, **sans
modifier ni désactiver le test d'intégrité**. Les 36 tests annoncés par Codex
restent distincts de ces 22 tests actuellement disponibles.

**Aucune nouvelle mesure sur les jeux gelés n'a été lancée.** Les contrôles
effectués portent sur les empreintes, la structure des fichiers et les tests
logiciels existants. Les fichiers conservent leur statut historique de jeux
déjà consultés/mesurés ; leur récupération ne les rend pas indépendants du
développement passé.

Le fichier `ocr_baseline_v1.csv` contient des prédictions de baseline, pas une
vérité terrain : `ocr_gold_v1.csv` n'est toujours pas disponible. Le gold
indépendant de rappel d'alignement, les annotations d'obligations, les sources
NER/CoNLL et le cahier des charges complet restent également nécessaires pour
achever les volets scientifiques correspondants.

**Prochaine tâche exacte :** poursuivre l'audit des exigences du cahier des
charges complet et récupérer les sources des composants manquants (notamment
obligations/NER/CoNLL et les trois scripts Codex refusés). Le blocage de la suite
logicielle locale est désormais levé ; ne pas confondre ce résultat avec la
validation scientifique complète du projet.

## Étape 6 — démonstration restaurée, HTTP vérifié, contrôle sur développement

**État actuel : alignement complet, démo CLI et adaptateur HTTP local fonctionnels.**
Les deux sources fournies ont été inspectées puis copiées à leur emplacement
attendu, sans aucune modification :

| Source récupérée | SHA-256 |
|---|---|
| `src/evaluation/baseline_bm25.py` | `97adc260105f42f47b6ee7fb6cdba0d18bc27926a18df58219f2cb9face25588` |
| `src/demo/repondre.py` | `ce84affd5943b92eb8cc0c19199a5d020dc849efae8a06715b396c3e3ab25b9c` |

Manifeste et diagnostic des intitulés :
`reports/reprise/restauration_demo_manifest.json`.
Les 728 fichiers de données récupérés ont encore été vérifiés après les
exécutions : tous inchangés. Les suppressions effectuées par l'utilisateur
dans ce suivi ont été respectées.

### Démonstration et nouveaux livrables HTTP

- La question complète sur le préavis renvoie **14 bis, page PDF 279**.
- La question sur la capitale de la Tunisie déclenche l'abstention.
- La formulation avec le sigle « CDI » conserve la fausse abstention connue.
- La question arabe utilisée pour vérifier le transport UTF-8 renvoie 14 bis
  via HTTP. Ce cas de démonstration n'est pas une annotation ou une mesure de test.
- Seuil historique **9,085**, `ACTIVER_STOP_TUN=False` : aucun réglage effectué.
- Index de cette implémentation : 496 lignes FR et 491 lignes AR, à distinguer
  des 498/515 lignes des corpus. Les fonctions d'intitulé excluent certains
  en-têtes et fusionnent des suffixes. Comparaison avec les clés d'alignement :
  56 divergences d'intitulé FR et 74 AR, incluant les en-têtes non reconnus ;
  ce ne sont pas 130 erreurs de pertinence mesurées.

Un **nouvel adaptateur de reprise** `api.py` et un lanceur `demarrer.ps1` ont
été ajoutés autour de la démo existante. Ce ne sont pas des fichiers retrouvés
de la session Codex. Routes : `GET /health`, `POST /repondre`.
Questions JSON FR/AR, validation des entrées, extraits/pages, abstention et
latence. Bibliothèque standard, écoute locale sur `127.0.0.1` seulement.

Lancement réellement vérifié : `.\demarrer.ps1 -Port 18765`.
Quatre requêtes réelles réussies : health, préavis FR, hors périmètre et AR.
Réponses sauvegardées dans `reports/reprise/verification_http.json`.
Une première tentative sur 8765 recevait une réponse ne correspondant pas à
l'adaptateur ; elle n'a pas été retenue comme succès. La vérification a été
faite sur 18765 avec le schéma attendu. Les processus de vérification lancés
par la reprise ont ensuite été arrêtés.

### Contrôle de développement et tableaux produits

Script ajouté : `src/evaluation/evaluer_dev_reprise.py`.
Il lit uniquement le dev v2 dont l'empreinte est vérifiée, ne modifie pas les
paramètres, ne lit aucun test gelé et ne remplit aucune annotation.

Commande exécutée :

```powershell
python src/evaluation/evaluer_dev_reprise.py --rapports reports/reprise/demo_dev
```

Le dossier contient le JSON détaillé, trois tableaux CSV et le CSV des erreurs,
avec mention explicite `developpement_non_independant`.
Les résultats ont été reproduits lors de deux exécutions du calcul.

| Mesure dev v2 | Sans seuil de score | Seuil historique 9,085 |
|---|---:|---:|
| Questions | 56 | 56 |
| Questions dans / hors périmètre | 27 / 29 | 27 / 29 |
| Article correct en premier | 21/27 | 21/27 |
| Article présent dans le top 5 | 23/27 | 21/27 |
| Hors périmètre correctement refusé | 0/29 | 27/29 |
| Fausses abstentions | 0/27 | 4/27 |
| Erreurs selon le critère ci-dessous | 35 | 8 |

Une erreur est ici un hors périmètre accepté, une fausse abstention ou un
premier article incorrect. Le seuil évite 27 erreurs selon ce critère, mais les
4 fausses abstentions concernent des questions dont le premier résultat était
déjà incorrect ; « 0 erreur nouvellement introduite » selon ce critère ne
signifie donc pas absence d'effet défavorable. Le rappel@5 perd deux réussites.

Les quatre catégories automatiques observées entre les variantes sont :
référence absente du top 5, article voisin classé devant, hors périmètre accepté
et abstention à tort. Chaque variante n'en présente que trois avec effectif
non nul. Le CSV des erreurs contient 43 lignes (35 + 8), avec des questions
présentes dans les deux variantes : ne pas annoncer 43 erreurs indépendantes.

Ventilation du dev : FR = 21 dans / 23 hors, tunisien = 6 dans / 3 hors,
AR = 0 dans / 3 hors. Le rappel pour l'arabe n'est pas défini sur ce jeu.
Ce contrôle ne reproduit pas le bilan Codex « 30 erreurs, 21 évitées, 9 restantes »
sur un autre jeu/version. Les tableaux sont utilisables pour le développement,
pas comme livrables finaux mesurés sur test indépendant.

### Tests exécutés et véritables blocages

`python -m pytest -q -p no:cacheprovider`, Python 3.12.2 et pytest 9.2.0 :
**20 tests réussis, 1 xfail, 1 échec**, 17 sous-tests réussis, 2,32 s, sortie 1.

- Les 10 tests d'alignement et 5 tests HTTP passent.
- La suite historique se collecte désormais : 5 réussites, le cas CDI en xfail,
  et le contrôle d'intégrité des jeux gelés en échec.
- Échec réel : `data/test_locked/questions_reference_v2.csv` absent. Le test
  n'a pas été ignoré ou modifié. Les candidats OCR et leur baseline manquent aussi.
- Les 36 tests Codex ne sont toujours pas disponibles sous leur forme originale.

**Prochaine tâche exacte :** récupérer `data/test_locked/`, notamment
`questions_reference_v2.csv`, `ocr_candidats_v1.csv` et `ocr_baseline_v1.csv`,
vérifier leurs empreintes contre le journal et relancer le test d'intégrité.
Leur récupération n'autorise pas à les réutiliser pour régler le seuil.

Restent également : sources Codex des trois modifications refusées, extraction
d'obligations et annotations, NER/CoNLL avec référence publiée, notebooks 02/04,
cahier des charges complet et livrables de présentation historiques. Aucun
score indépendant ni annotation humaine n'a été inventé pour les remplacer.

## Étape 5 — corpus arabe récupéré et alignement complet reproduit

**État actuel : l'alignement est exécutable sur les vrais corpus.** Les mentions
antérieures de corpus AR ou PDF manquant décrivent les étapes précédentes.
La démonstration BM25/API, les scripts Codex et les jeux de test indépendants
restent à récupérer ; le projet complet n'est pas déclaré terminé.

### Récupération et provenance

Source fournie : `C:\Users\Moham\Downloads\data-20261027T220600Z-1-001\data`.
Ce dossier contient 728 fichiers :

- 515 articles dans `processed/articles_ar.csv`, empreinte
  `77fe24b3d3ffc5923fd42fe4298521ebdbcec5f7af001ccd576a90fa69846022` ;
- PDF source `raw/arabic/majallat_al_shughl_2019.pdf`, 291 pages,
  1 170 023 octets, empreinte
  `de17529ea734212b6efcec0d796762f39fefbf97455a573ca402bf83c74bc467`,
  identique à celle consignée dans le journal historique ;
- 291 images PNG, 136 pages OCR arabes, 155 pages OCR arabe/français,
  128 caches OCR de bandes ;
- tables de corrections, notes et vérifications, résumés et anciens exports.

Recherche complémentaire demandée à la racine
`C:\Users\Moham\Downloads\data-20261027T220600Z-1-001` :
inventaire récursif avec fichiers cachés effectué. Cette racine ne contient que
le sous-dossier `data`, soit les mêmes 728 fichiers. Aucun script `.py`, notebook
`.ipynb`, archive imbriquée, dossier `src` ou `test_locked`, ni fichier de
questions/gold/baseline n'a été retrouvé. Les scripts BM25/démo et Codex ne sont
donc pas présents ailleurs dans cet export.

**725 fichiers ajoutés**, 3 déjà présents et identiques, aucun conflit.
Les 728 fichiers ont été contrôlés par SHA-256 après copie, puis après les
exécutions : **aucun fichier récupéré n'a été modifié**.
Manifeste : `reports/reprise/recuperation_data_manifest.json`.
Les tables de vérification remplies sont héritées ; aucune annotation humaine
n'a été créée ou revalidée par cette reprise.

### Vérifications du corpus

- Schéma nécessaire au notebook présent, aucune ligne CSV AR mal formée.
- 515 identifiants AR uniques ; aucun numéro absent de 1 à 446 ; aucun chapitre vide.
- 38 lignes ont `abroge=True`, 20 ont `plage=True`.
- Les identifiants/pages AR des 160 références de développement correspondent
  au corpus récupéré.
- AR-367 a une métadonnée `longueur=362` pour un texte de 190 caractères.
  La colonne `corrections` signale le déplacement d'une note vers AR-364 :
  la longueur n'a pas été recalculée après ce changement. Le fichier reste intact.
- `corrections_fr.csv` contient 15 lignes. `notes_bas_pages.csv` en contient 39,
  avec 30 statuts indiquant encore un rattachement à effectuer. Ce fichier
  récupéré ne justifie pas à lui seul la clôture historique « 0 note à rattacher ».
  La chaîne de segmentation/correction reste à retrouver avant de réinterpréter
  ces statuts ou d'appliquer des corrections.

### Exécution réelle et reproduction

Un lanceur local a été ajouté : `src/executer_alignement.py`. Il exécute les
cellules du notebook v6 sans serveur Jupyter et permet un dossier d'export distinct.
Commandes réellement exécutées avec sortie 0 :

```powershell
python src/executer_alignement.py
python src/executer_alignement.py --sortie reports/reprise/reproduction_v6
```

Environnement : Python 3.12.2, pandas 2.2.2, NumPy 2.4.1, Windows.
Versions consignées dans `reports/reprise/environnement_alignement.json` ;
dépendances ciblées dans `requirements-alignement.txt`.

Résultat : **519 lignes de sortie**, composées de :

| Statut calculé | Effectif |
|---|---:|
| Apparié | 494 |
| Abrogé (plage) | 21 |
| Hors Code (loi n° 66-27) | 4 |
| Doublon à trancher | 0 |
| Absent du français | 0 |

Six contrôles d'années sont signalés : **AR-18, AR-52, AR-335, AR-364, AR-417,
AR-419**. Ce résultat diffère des 3 annoncés dans `PIPELINE.md`, mais son effectif
correspond au résumé récupéré. Les contrôles sont des alertes automatiques,
pas des erreurs juridiques confirmées.

Les trois exports v6 de la seconde exécution sont **identiques octet par octet**
à ceux de la première. La reproductibilité technique est donc vérifiée sur ces
entrées. Les sorties historiques sont conservées.

### Comparaison et limites scientifiques

- Les 519 positions, clés, références AR/FR, pages, statuts et lignes FR sont
  identiques à l'ancien `alignement_fr_ar.csv`.
- Huit lignes diffèrent dans les champs auxiliaires : six extraits FR reflètent
  les corrections textuelles ; le contrôle d'années porté par AR-367 apparaît
  maintenant sur AR-364, conformément au déplacement de note tracé dans le corpus.
- L'export réel concorde avec les 60 références dev v1 et les 100 références
  dev v2. **Ce n'est pas un résultat sur test indépendant.**
- 69 étiquettes `article_fr` restent sans suffixe alors que la clé d'appariement
  en porte un ; les clés et positions sont conservées, les identifiants seuls
  ne doivent pas servir de référence unique.
- 17 paires ont `abroge=True` côté AR tout en portant le statut d'appariement
  `apparié`. Ne pas confondre statut d'appariement et statut juridique de l'article ;
  aucune reclassification juridique automatique n'a été appliquée.
- Le rappel global, la précision et F1 sur test indépendant restent **non mesurés**.
  Ils sont `null`, avec motif explicite, dans le rapport.

Rapport : `reports/reprise/audit_alignement_complet.json`, produit par
`python src/auditer_reprise.py`, avec contrôle des données, comparaison des
exports, empreintes d'exécution et résultat des deux exécutions.

### Tests, blocages et prochaine tâche

La suite complète a été tentée avec pytest 9.2.0, dans Python disposant de pandas,
en réutilisant l'installation temporaire de pytest sans installation globale :

```text
python -m pytest -q -p no:cacheprovider --continue-on-collection-errors
10 passed, 1 error, 6 subtests passed in 1.10s
```

Sortie **1** : la suite n'est pas entièrement réussie.
`tests/test_evaluation.py` échoue toujours à la collecte sur
`ModuleNotFoundError: baseline_bm25`. Les 10 tests d'alignement passent ;
les sous-tests ne sont pas 6 tests de corpus supplémentaires.

Le répertoire téléchargé fournit uniquement les données. Une recherche ciblée
des dossiers/archives voisins n'a pas retrouvé d'export `src`, `notebooks` ou
`reports` supplémentaire. Il n'y a toujours pas de `.git` dans le projet.

**Prochaine tâche exacte :** récupérer `src/evaluation/baseline_bm25.py`,
`src/demo/repondre.py` et `data/test_locked/` pour restaurer la démo et ses tests,
ainsi que les scripts de la session Codex. Pour la provenance des transformations,
récupérer les notebooks 02/04 et le cahier des charges complet LegalTN.
L'évaluation indépendante et les annotations humaines manquantes restent
distinctes de la restauration technique désormais accomplie pour l'alignement.

## Étape 4 — notebooks d'alignement récupérés et règles testées

Cette mise à jour remplace les mentions d'absence des notebooks 03 dans les
étapes précédentes. Trois fichiers fournis depuis `Downloads` ont été copiés
dans `notebooks/`, sans changement :

| Version originale | SHA-256 |
|---|---|
| `03_alignement_fr_ar.ipynb` | `9e3e25e9392d64db2fefd5093542f6923606b6677465b5ec048efe7504f14bde` |
| `03_alignement_fr_ar_v4.ipynb` | `f81b76b791b31bd2838fd2ac696389bc2809b8cac7468a26e8ba14895df89aa9` |
| `03_alignement_fr_ar_v5.ipynb` | `7214f6a6702145513cae58060922a81705e66351f4c2afcef4b2fa206f1ce0df` |

Comparaison du code :

- La version initiale ne traite pas « Article premier » et ne filtre pas les
  pages 288–289 de promulgation.
- La v4 ajoute ces traitements et le suivi des lignes françaises non retenues.
- La v5 reprend les règles v4 et utilise `articles_fr_corrige.csv` en priorité.
  Elle correspond au notebook de référence de `PIPELINE.md`.
- Les trois notebooks ont chacun 7 cellules, dont 5 de code, sans compte
  d'exécution ni sortie enregistrée. Analyse syntaxique effectuée sans erreur.

**Contrôle exécuté avec les règles originales v5 :**

- 498 entrées françaises, dont 4 hors Code ; 494 clés françaises distinctes
  dans le Code, aucune clé non reconnue ni ambiguë sur ce corpus.
- Les fonctions `cle_ar` et `cle_fr` retrouvent la ligne française attendue pour
  les 60 références dev v1 et les 100 références dev v2, suffixes inclus dans
  les clés calculées.
- Ce sont des contrôles de développement hérités, pas un test indépendant ni
  une mesure du rappel global. Le fichier arabe segmenté est toujours absent.
- Commande exécutée avec sortie 0 : `python src/auditer_reprise.py`.
  Rapport conservé : `reports/reprise/audit_alignement_v5.json`.

**Correction réalisable effectuée dans une nouvelle version v6 :**

1. Repérage de la racine à partir de `data/processed/` ou `data/raw/`, plutôt
   que repli silencieux dans un sous-dossier `LegalTN` lorsque `data/raw/` manque.
2. Exports nommés `alignement_fr_ar_v6.csv`, `alignement_resume_v6.json` et
   `alignement_echantillon_image_v6.csv`. Vérification de leur absence avant
   toute écriture, puis création exclusive : aucun export existant, notamment
   un échantillon annoté, n'est écrasé. Les règles des cellules 2 à 4 sont
   strictement identiques à celles de v5.

Il s'agit d'une correction opérationnelle locale, **pas** de la récupération
du changement refusé dans `alignement.py`, qui reste absent. La v6 ne prétend
pas corriger les défauts historiques des étiquettes FR ou des statuts abrogés.

**Tests réellement exécutés :**

`python -m unittest discover -s tests -p test_alignement_notebook.py -v`

Python 3.12.2, pandas 2.2.2 : **10 tests réussis** lors de la dernière exécution
(0,178 s). Sept tests couvrent les règles v5 : suffixes, article premier,
exclusion de promulgation, ambiguïtés, absences/abrogations, années et refus
de réutilisation d'une ligne FR. Trois tests couvrent la conservation des règles
v5, le repérage de racine et les exports protégés v6, y compris une réexécution.
Les fixtures sont synthétiques ; les seuls exports effectués sont temporaires,
hors corpus du projet. Aucun fichier d'alignement réel n'a été généré.

La suite historique `tests/test_evaluation.py` reste bloquée par les modules
BM25/démo absents ; ces 10 tests ne confirment pas les 36 tests annoncés par Codex.
Le statut Git reste indisponible, faute de `.git`.

**Prochaine tâche exacte :** récupérer `data/processed/articles_ar.csv`,
vérifier son schéma (`article_id`, `page`, `abroge`, `texte_ar`,
`note_amendement`) et sa provenance, puis exécuter la v6 sur les vrais corpus.
Si le CSV n'est plus disponible, récupérer `02_segmentation_v15.ipynb` et ses
tables de corrections pour le régénérer fidèlement ; ne pas reconstruire un
corpus arabe définitif depuis les seules références dev.

## Mise à jour — fichiers complémentaires fournis

Nouvelle recherche demandée dans ce dossier après récupération : inventaire
récursif avec fichiers cachés, **20 fichiers au total**. Aucun nouveau fichier
source retrouvé, aucune archive imbriquée et aucun `.git`. Les fichiers
`articles_ar.csv`, `alignement.py`, `evaluer_obligations.py`,
`preparer_lots_independants.py`, `baseline_bm25.py`, `repondre.py`, `api.py`,
`tests/test_api.py`, `tests/test_alignement.py` et le PDF original restent absents.
Les seuls fichiers dont le nom contient « alignement » sont les deux CSV de
développement, qui ne contiennent pas l'implémentation du traitement.

Le même jour, l'utilisateur a fourni six fichiers supplémentaires. Ils ont été
copiés **sans changement de contenu**, après vérification de l'absence de conflit :

| Source dans `C:\Users\Moham\Downloads` | Copie dans le projet |
|---|---|
| `texte_travail.json` | `data/processed/texte_travail.json` |
| `articles_fr.csv` | `data/processed/articles_fr.csv` |
| `articles_fr_corrige.csv` | `data/processed/articles_fr_corrige.csv` |
| `questions_dev_v2.csv` | `data/dev/questions_dev_v2.csv` |
| `01_data_exploration.ipynb` | `notebooks/01_data_exploration.ipynb` |
| `Guide_Revue_Bronze.pdf` | `docs/Guide_Revue_Bronze.pdf` |

Les sections suivantes décrivant une copie de 10 fichiers constituent **l'audit
initial**, avant cet apport. Le corpus français, le texte de travail, le notebook
01 et le guide Bronze sont désormais présents. Le code applicatif Codex, le
corpus arabe segmenté, les notebooks 02/03/04 et les jeux de test restent absents.

Le script `src/auditer_reprise.py` a été ajouté pour reproduire les contrôles de
ces fichiers en lecture seule, sans dépendance externe ni exécution du notebook.
Commande exécutée : `C:\Python312\python.exe src/auditer_reprise.py`, sortie 0.
Rapport généré : `reports/reprise/audit_donnees_recuperees.json`, avec les empreintes
des six fichiers récupérés et des trois CSV de développement consultés.

### Constats de l'étape 3 — récupération et audit des données

- **Texte de travail :** 291 clés de page, exactement 1 à 291, toutes associées à
  des chaînes de caractères ; la page 136 est vide. Il s'agit du texte de travail
  après traitements du notebook, pas d'un nouvel OCR ni du PDF original.
- **Corpus français :** 498 lignes dans chaque version ; ordre, numéros,
  identifiants et pages identiques ; 34 textes diffèrent. Les longueurs stockées
  concordent avec les textes et aucun texte n'est vide ou strictement dupliqué.
  Ces 34 différences ne sont pas assimilables aux « 15 corrections » historiques :
  elles incluent notamment des notes éditoriales et demandent la chaîne de
  transformation originale pour être expliquées intégralement.
- **Identifiants FR :** 425 identifiants distincts, 34 identifiants répétés,
  soit 73 occurrences supplémentaires. Les suffixes sont souvent présents dans
  l'en-tête textuel mais absents de `article_id`. Quatre lignes aux pages 288–289
  appartiennent au texte de promulgation, selon la documentation historique.
  Ne pas construire un dictionnaire par `article_id` seul ni supprimer ces lignes
  comme des doublons de texte.
- **Numérotation FR :** 21 numéros n'ont pas de ligne individuelle :
  272–277, 325–332, 336–337, 392–396. Cette absence ne prouve pas une perte OCR :
  les plages et têtes groupées abrogées doivent être vérifiées sur le PDF.
- **Références dev :** les 60 références v1 et les 100 références v2 retrouvent
  toutes le bon couple `article_id` / page à la position `fr_ligne` (index à partir
  de zéro, hors en-tête). C'est un contrôle de compatibilité des fichiers ; ni
  la justesse du suffixe textuel ni l'équivalence juridique AR/FR n'ont été évaluées.
- **Questions dev v2 :** 56 questions, dont 27 dans le périmètre et 29 hors
  périmètre ; 44 FR, 9 tunisiennes, 3 AR. Aucun identifiant ni texte de question
  répété. SHA-256 identique à l'entrée du journal :
  `9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8`.
  Ce jeu déjà utilisé pour calibrer n'est pas un nouveau test indépendant.
- **Obligations :** 199 phrases candidates sur 200 sont des extraits exacts
  retrouvés de manière unique dans l'article/page du corpus corrigé. D045
  (`FR-341`, p. 179) existe dans la version initiale mais est interrompue dans la
  version corrigée par `(*) Verbe d’état ajouté.`. Les données restent inchangées ;
  il faut récupérer les notes et le notebook de correction avant de décider
  quel texte est la référence. Aucun champ d'annotation n'a été complété.

### Notebook et environnement

- 29 cellules, dont 16 cellules de code : analyse syntaxique exécutée, aucune
  erreur détectée. **Le notebook n'a pas été exécuté.**
- Ses sorties historiques proviennent notamment de `/home/claude/LegalTN`, avec
  un noyau Python 3.13.16. Elles décrivent une exploration intermédiaire
  (490 têtes AR, 5 numéros à vérifier), pas la segmentation finale.
- Le notebook écrit `texte_travail.json`, un index provisoire, des statistiques,
  images et caches OCR. Le relancer n'est pas nécessaire pour exploiter les
  fichiers récupérés et pourrait remplacer le texte de travail fourni.
- Son repérage de racine cherche `data/raw/`. Sans ce dossier ni `LEGALTN_ROOT`,
  le repli crée un sous-dossier `LegalTN` relatif au répertoire courant.
  Lors d'une future exécution contrôlée, définir explicitement
  `$env:LEGALTN_ROOT = 'C:\Users\Moham\Downloads\LegalTN'`.
- PyMuPDF, pandas, NumPy et Pillow sont présents dans Python 3.12.2.
- Tesseract est présent à `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  `--list-langs` a réellement été exécuté : seuls `eng` et `osd` sont installés.
  Les packs `ara` et `fra` requis sont absents ; le PDF de 291 pages manque aussi.

### Vérification et suites

Le script d'audit a été exécuté et son JSON relu. Les six copies sont identiques
aux fichiers fournis ; les neuf fichiers initiaux autres que `experiments.md`
sont inchangés. Une entrée d'audit a été ajoutée à la fin de `experiments.md`,
sans modifier ses entrées historiques. Les contrôles de données et de syntaxe ne sont pas les tests
applicatifs : ceux-ci restent bloqués par `baseline_bm25.py` et `repondre.py`
absents. Aucun nouveau résultat de modèle, test HTTP ou annotation humaine.

Le README décrit maintenant la seule commande de contrôle réellement disponible.
Les sources manquantes prioritaires sont toujours :

1. Le dépôt de la session Codex et ses trois scripts à reprendre, avec les
   modifications locales et dépendances.
2. `articles_ar.csv`, `02_segmentation_v15.ipynb`,
   `04_partie_francaise_corrections_v2.ipynb`, `03_alignement_fr_ar_v5.ipynb`,
   les tables de notes/corrections et le PDF `majallat_al_shughl_2019.pdf`.
3. `src/evaluation/baseline_bm25.py`, `src/demo/repondre.py`, les jeux gelés,
   les sources API/CoNLL et le cahier des charges original LegalTN.

Prochaine tâche : comparer les fichiers récupérés suivants à leurs références
historiques, puis reprendre les correctifs sur les sources originales. Ne pas
produire `articles_ar.csv` à partir de l'index provisoire du notebook 01 :
cela omettrait les corrections de segmentation des notebooks suivants.

## Conclusion de l'audit initial

**La copie disponible est incomplète. La reprise du code de la session Codex est bloquée par l'absence des sources.**

À l'ouverture, ce dossier contient exactement 10 fichiers. L'archive voisine
`C:\Users\Moham\Downloads\LegalTN.zip` contient les mêmes 10 fichiers, identiques
octet par octet. La décompresser à nouveau ne récupérerait aucun élément manquant.
Il n'existe ni `.git`, ni notebook, ni corpus complet, ni application dans cette copie.

Le compte rendu Codex fourni dans la demande n'est pas une preuve d'exécution
locale. Ses chiffres diffèrent de ceux de la documentation présente. Il faut
récupérer la version correspondante avant de corriger ou de reproduire ses résultats.
Aucun pourcentage global d'achèvement fiable ne peut être calculé.

## Étape 1 — audit terminé sur les éléments accessibles

- Inventaire récursif, y compris fichiers cachés ; lecture des documents et du seul fichier Python.
- Lecture des quatre CSV, contrôle de structure, doublons et champs d'annotation.
- Comparaison intégrale des fichiers avec l'archive voisine.
- Examen de `PIPELINE.md`, de tout `experiments.md` et des commandes de démonstration.
- Aucun `AGENTS.md`, manifeste de dépendances ou configuration CI dans cette copie.
- Python disponible : `C:\Python312\python.exe`, version 3.12.2.
- `git status --short` et `git log -6 --oneline` échouent : « not a git repository ».
- Les neuf fichiers modifiés / 636 lignes ajoutées rapportés par Codex sont invérifiables.
- Aucun fichier initial n'a été modifié ni supprimé à cette étape.

## Documents PDF et exigences

Le cahier des charges original LegalTN est absent du dossier et de l'archive.
Les PDF voisins dont le nom évoque un cahier des charges concernent d'autres
projets : ils ne constituent pas les spécifications de LegalTN.

Un document pertinent a été retrouvé et lu intégralement :
`C:\Users\Moham\Downloads\Guide_Revue_Bronze.pdf` (16 pages).
Ce guide fournit les exigences Bronze ci-dessous ; il ne remplace pas le cahier
des charges complet du projet. La conformité aux autres phases reste à auditer.

| Exigence vérifiée dans le guide | Source | État de cette copie / travail restant |
|---|---|---|
| Alignement par numérotation, précision et rappel | p. 10 | Deux CSV de développement présents ; code, corpus et gold indépendant absents |
| Obligations par règles, F1 par rôle | p. 10 | Guide et 200 candidats présents ; annotations, extracteur et évaluateur absents |
| NER par CRF, F1 par span | p. 10 | Code, modèles et jeux absents |
| BM25 avec extrait cité en français, rappel@5 et citation exacte | p. 10 | Documenté historiquement ; implémentation et références absentes |
| Démo intégrée, entrée imprévue, tunisien, hors périmètre, étapes visibles, latence, sources | p. 7 | Application/API et lanceur absents ; pas de vérification HTTP possible |
| Démo classique sans LLM ni API payante | p. 7 | À vérifier sur les sources récupérées |
| Métrique de test comparée à une baseline, résultat dev séparé | p. 5, 8 | Aucun résultat reproductible ici |
| Trois tableaux : composants, langues/scripts, erreurs | p. 8–9 | Tableaux et scripts absents |
| Au moins 30 erreurs par composant principal, 4 à 6 catégories, CSV entrée/sortie/référence | p. 6, 9 | Résultats historiques dans le journal ; CSV correspondants absents |
| Reproduction d'un résultat publié, valeur publiée/obtenue et écart expliqué | p. 6 | Baseline CoNLL-2002 rapportée par l'utilisateur, fichiers absents |
| Corpus chiffré, cartes de données, licence, séparation et gel des jeux | p. 4, 13 | Documentation partielle ; corpus, cartes et jeux de test absents |
| Guide d'annotation, kappa et effectif | p. 4, 13 | Guide obligations présent ; aucune double annotation disponible |
| Dépôt Git, tag bronze, README d'installation et lancement | p. 13 | Absents ; ne pas créer un historique de substitution |
| Slides PDF, vidéo de secours de 2 minutes | p. 3, 13 | Historiquement documentés, fichiers absents |
| Kanban, journal, responsable, déclaration d'usage IA, cartes système/modèles | p. 13 | Journal présent ; autres pièces absentes |

La vérification des polices incorporées aux PDF est également demandée dans la
reprise. Elle attend les PDF de présentation ; le guide n'est pas le livrable
à contrôler.

## Fichiers de la session Codex et modifications refusées

Recherche effectuée dans toute l'arborescence locale et dans l'archive.

| Fichier attendu | État |
|---|---|
| `alignement.py` | Absent ; modification refusée d'une ligne invérifiable |
| `evaluer_obligations.py` | Absent ; modifications refusées invérifiables |
| `preparer_lots_independants.py` | Absent ; ajout prévu d'environ 80 lignes invérifiable |
| `tests/test_alignement.py` | Absent |
| `api.py` | Absent |
| `tests/test_api.py` | Absent |
| `reproduire_baseline_conll.py` | Absent |
| `preparer_dossier.py` | Absent |
| `demarrer.ps1` | Absent |
| `generer_video.py` | Absent |
| `reports/bronze/CARTES_ET_PROTOCOLE.md` | Absent |

L'absence des fichiers dans cette copie ne prouve ni l'annulation ni
l'enregistrement des modifications dans le dépôt utilisé par Codex. Aucun de ces
modules ne sera recréé à partir d'hypothèses : cela risquerait de remplacer le
travail à préserver.

## Données effectivement contrôlées

Ces constats sont des contrôles de fichiers, pas de nouvelles mesures de performance.

| Fichier | Constat local |
|---|---|
| `data/dev/alignement_dev_v1.csv` | 60 lignes ; 57 verdicts `correct`, 3 `correct_mais_statut_incomplet` ; 60 champs de validation renseignés ; 5 catégories de suffixe manquant et 3 de statut incomplet |
| `data/dev/alignement_dev_v2_a_annoter.csv` | 100 lignes déjà renseignées malgré le nom ; 100 verdicts `correct` ; 10 catégories de suffixe manquant et 2 de statut incomplet |
| `data/dev/obligations_candidats_dev_v1.csv` | 200 phrases candidates ; `qui`, `modal`, `quoi`, `quand`, `commentaire` entièrement vides |
| `data/dev/obligations_modele_v1.csv` | En-tête seul, zéro annotation |

- Aucune ligne CSV mal formée détectée.
- Aucun doublon d'identifiant d'exemple ; aucun doublon d'article AR ou de ligne FR dans chacun des deux jeux d'alignement.
- Aucun chevauchement entre dev alignement v1 et v2 sur `cle`, `article_ar` ou `fr_ligne`.
- Ce contrôle entre deux jeux de développement ne prouve pas l'indépendance d'un test absent.
- Aucun doublon exact de phrase dans les 200 candidats obligations.
- Les validations sont **héritées** des CSV et du journal ; aucune relecture humaine ni vérification sur image n'a été effectuée pendant cet audit.
- Les dernières entrées du journal indiquent la validation des 60 lignes v1 et la dictée des 100 verdicts v2, dont 97 en bloc. Les entrées antérieures disant « non validé » ne décrivent donc pas le dernier état documenté.

## Résultats historiques, incertitudes et risques scientifiques

| Élément | Source et statut |
|---|---|
| 509 entrées AR, 485 appariements, 6 numéros absents | Compte rendu Codex fourni ; non reproduit, corpus absent |
| 515 articles AR, 494 appariements, 0 numéro absent | `PIPELINE.md` ; autre état documenté, non reproduit |
| 30 erreurs avant calibration, 21 évitées, 9 restantes | Compte rendu Codex ; données, seuil et code absents |
| 33 erreurs sur 108 questions dev v5, 4 catégories | Journal local ; CSV et démo absents, non reproduit |
| Précision d'alignement 30/30, OCR 29/30, résultats BM25 | Journal historique seulement ; golds, prédictions et corpus absents |
| 36 tests réussis | Compte rendu Codex seulement ; suite absente |
| 6 tests réussis, 1 xfail | Dernière entrée du journal local ; 7 fonctions de test présentes, résultat à ne pas présenter comme actuel |
| Écart de reproduction CoNLL-2002 | Signalé par la demande ; valeurs et explication indisponibles, à récupérer sans les remplacer |
| Rappel/F1 d'alignement et F1 obligations | Non mesurables ici faute de référence indépendante / d'annotations |
| Kappa | Non calculable sans annotations indépendantes de plusieurs annotateurs |

Problèmes repérés à conserver lors de la reprise :

1. Suffixes français absents de certaines étiquettes : les CSV présents en gardent
   des exemples. Ne pas confondre défaut d'étiquette et erreur d'appariement ;
   conserver l'identité par article, suffixe, page et ligne source.
2. Le journal décrit un chevauchement de trois articles (104, 225, 226) entre dev
   v3 et test v4. L'indépendance par article de ce résultat historique ne peut
   pas être revendiquée ; la confirmer sur les fichiers récupérés.
3. Le journal signale plusieurs mesures sur test v2 et des tests déjà consommés.
   Ne pas utiliser ces résultats pour régler un nouveau seuil, ni présenter un
   nouveau test comme indépendant si ses sources ont servi au développement.
4. Les candidats obligations proviennent d'un filtrage lexical. Évaluer seulement
   les 119 candidats restants ne mesurerait pas le rappel sur les obligations sans
   ces marqueurs. Des phrases différentes d'un même article ne garantissent pas
   non plus l'indépendance entre développement et test.
5. Les échecs du tunisien et l'instabilité des seuils figurent dans le journal ;
   ils ne doivent pas être masqués par une moyenne globale.

## Tests et démarrage

- Commande exécutée : `C:\Python312\python.exe -m pytest -q`.
- Résultat initial : sortie 1, `No module named pytest`. Aucun test exécuté.
- Le seul fichier de tests importe `baseline_bm25` et `repondre`, tous deux
  absents ; il dépend aussi de `data/processed/` et `data/test_locked/`, absents.
- `demo_evaluation.sh` appelle trois scripts absents. Les dépendances Python
  originales ne sont pas définies dans cette copie.
- Pytest 9.2.0 installé dans un environnement temporaire isolé, sans modifier
  Python global : `C:\Users\Moham\AppData\Local\Temp\legaltn-audit-20261027`.
- Commande exécutée dans le dossier du projet :
  `& 'C:\Users\Moham\AppData\Local\Temp\legaltn-audit-20261027\Scripts\python.exe' -m pytest -q -p no:cacheprovider`.
  Exécution avec `PYTHONDONTWRITEBYTECODE=1` et
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
- Résultat : sortie 2, une erreur de collecte en 0,38 s,
  `ModuleNotFoundError: No module named 'baseline_bm25'`
  (`tests/test_evaluation.py`, ligne 22). **Aucun test exécuté ni réussi.**
- Commande de démo essayée :
  `C:\Python312\python.exe -I src/demo/repondre.py "Quelle est la capitale de la Tunisie ?"`.
  Résultat : sortie 2, fichier `src/demo/repondre.py` introuvable.
- Aucun test HTTP, lancement API, rendu de rapport, contrôle de police ou
  reproduction d'expérience n'est déclaré réussi.

## Étape 2 — vérification finale des possibilités locales

L'installation de l'outil de test a permis de confirmer que le blocage vient
des sources absentes. Il n'est pas possible de tester les trois corrections
refusées ni les 36 tests de Codex avec cette copie.

Après les commandes de vérification, les 10 fichiers initiaux ont été comparés
de nouveau à l'archive : **tous sont inchangés octet par octet**. Le seul fichier
ajouté au projet est `PROJECT_PROGRESS.md`. Aucun cache de tests, annotation,
corpus de remplacement ou résultat expérimental n'a été généré.

### Inventaire initial et empreintes SHA-256

| Fichier initial | SHA-256 |
|---|---|
| `PIPELINE.md` | `1fcc8ca3606331bd451b5eda4c214af9917852bbffaf9bc51ea0386043c1ce2d` |
| `experiments.md` | `0bd495d2f6b9505b5266d47fe1b386fb34847756d6d5f9b4a8dfe6735efc9afa` |
| `demo_evaluation.sh` | `acacdb31b212033905af4adeafee808ff5b09fae3b83595e5b1f654b701c39d8` |
| `tests/test_evaluation.py` | `f94bbe4947a443bf9d151bde20e6c3642927658d90af680f8469d30a71b68108` |
| `src/obligation_extraction/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `data/dev/alignement_dev_v1.csv` | `a208d2bef5207b987b538dc6408240da04010e4633354ab3dc0080c445f46e27` |
| `data/dev/alignement_dev_v2_a_annoter.csv` | `0cb92a177e95a98853ffb41db652b6dba2a363792b77a371997736d06e1569d0` |
| `data/dev/obligations_candidats_dev_v1.csv` | `8a1cac794bf52c568b3008cdb3e1b54bf7416b1cb5a21ca433ed9381b974ae76` |
| `data/dev/obligations_guide_annotation_v1.md` | `f9057b3a28fdae0f2dd6576c3949d5e7b5fb7ec4e775a4e5196f4ca50482c0ac` |
| `data/dev/obligations_modele_v1.csv` | `6114d7b558d05c96beff7e94f29c5c1532ba48200a85fbc65f0dfef04f346b71` |

Documents voisins contrôlés :

- `LegalTN.zip` : `1f21a6aad94dfa407889473f15506cb11789c315dd45537ce912b0af15c64d62`.
- `Guide_Revue_Bronze.pdf` : `a67a547bbd80cdd57aa24db4984a44112fcc7e9594d4f294c00ff5846c479540`.

## Étapes réalisées, partielles et restantes

**Réalisé pendant cette reprise :** audit de tous les fichiers disponibles,
contrôle de l'archive, lecture du guide Bronze, inventaire des absences, contrôles
structurels des CSV, distinction des sources de résultats et création de ce suivi.

**Partiel / hérité :** documentation du pipeline, historique expérimental,
annotations de développement d'alignement, préparation de l'annotation obligations.
Ces éléments ne suffisent pas à démarrer le système.

**Restant après récupération des sources :**

1. Lire le cahier original, vérifier la branche et les modifications non commitées,
   comparer les trois fichiers concernés avec leurs versions Git et les correctifs
   refusés si disponibles.
2. Réimplémenter seulement les parties manquantes et ajouter des tests de
   régression dans les suites existantes.
3. Vérifier corpus AR/FR, doublons, trous de numérotation, suffixes et références.
4. Préparer les lots indépendants, obtenir les annotations humaines nécessaires,
   vérifier les fuites, puis mesurer les métriques et la calibration.
5. Reproduire la baseline CoNLL-2002 avec ses versions, graines, données et
   évaluateur ; conserver le résultat obtenu et expliquer l'écart publié.
6. Finaliser démo/API, documentation, trois tableaux, graphiques, PDF, polices,
   vidéo et démarrage ; exécuter les tests unitaires et HTTP.
7. Actualiser ce suivi et le journal à chaque étape. Aucune publication ni
   aucun déploiement n'est autorisé par cette reprise.

## Protocole de reprise scientifique proposé

Ce protocole est préparatoire, non une expérience exécutée.

- Figer les versions du code, de l'environnement et des données avec leurs
  empreintes. Inventorier les exemples déjà consultés ou utilisés pour calibrer.
- Séparer les lots par article source, en regroupant ses traductions et doublons ;
  contrôler aussi les variantes de suffixes et les textes proches. Définir
  explicitement si les sous-articles appartiennent à la même famille de séparation.
- Choisir règles et seuils uniquement sur développement. Conserver les résultats
  avant/après sur les mêmes exemples, avec couverture, abstentions correctes,
  fausses abstentions et erreurs acceptées ; un gain dev n'est pas un gain test.
- Pour l'alignement, construire une référence indépendante des seules paires
  proposées, avec recherche des équivalents et marquage des cas sans équivalent.
  Donner TP, FP, FN, précision `TP/(TP+FP)`, rappel `TP/(TP+FN)` et
  F1 `2TP/(2TP+FP+FN)`, unités et effectifs. Un dénominateur nul doit être
  signalé comme non défini. Un échantillon ne démontre pas le rappel du corpus entier.
- Pour les obligations, annoter aussi les négatifs et les obligations sans marqueur
  lexical. Figer le critère d'appariement et calculer les résultats par rôle.
  Ne pas évaluer des champs vides comme des annotations négatives.
- Pour NER, utiliser les spans et types exacts ; pour retrieval, définir les
  questions éligibles et mesurer séparément rappel@5, citation et abstention.
- Présenter effectifs et résultats par langue/script, ainsi que limites de
  représentativité. Aucun score absent ne devient zéro.
- Catégoriser les erreurs réelles avec entrée, sortie, référence et statut
  automatique/humain. Si moins de 30 erreurs sont observées, donner ce nombre et
  l'écart au guide ; ne pas fabriquer d'erreurs ni de validations.
- La comparaison CoNLL exige le même jeu, split, prétraitement, modèle et
  évaluateur que la référence publiée ; toute différence doit être explicitée.

## Blocages et prochaine tâche exacte

**Blocage principal : récupérer la copie complète utilisée par Codex.**
Il faut son dossier avec les fichiers non commitées et, si disponible, `.git`,
ainsi que le cahier des charges original, le corpus et les jeux gelés, les
notebooks, les dépendances et les rapports. Un simple clone peut omettre les
modifications non commitées et les données ignorées ; l'archive actuelle est insuffisante.

Prochaine tâche exacte : ouvrir cette copie complète, exécuter `git status`,
inspecter les diffs de `alignement.py`, `evaluer_obligations.py` et
`preparer_lots_independants.py`, puis comparer avec cet inventaire **avant toute
restauration ou modification**.

Les annotations humaines et la relecture tunisienne restent des tâches humaines ;
leur absence ne sera pas compensée par des réponses inventées.
