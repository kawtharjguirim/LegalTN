# Pipeline LegalTN — version de référence (état au 27 octobre 2026)

> Reprise locale du 27 octobre : les versions originales 03, v4 et v5 sont
> récupérées. Une version de travail `03_alignement_fr_ar_v6.ipynb` conserve les
> règles v5, détecte la racine sans `data/raw/` et protège les exports existants.
> Elle écrit des sorties `_v6`. Le corpus AR et le PDF source ont depuis été
> récupérés ; deux exécutions complètes ont produit les mêmes exports octet par
> octet : 494 appariements, 21 lignes « abrogé (plage) », 4 hors Code, **6**
> contrôles d'années (et non les 3 mentionnés dans le bilan historique ci-dessous).
> Commande : `python src/executer_alignement.py --sortie reports/nouvel_alignement`.
> Les autres résultats historiques ci-dessous n'ont pas été recalculés.
> Voir `PROJECT_PROGRESS.md` et le README.

> Mise à jour suivante : `baseline_bm25.py` et `repondre.py` récupérés à
> l'identique ; démo CLI et adaptateur HTTP local de reprise fonctionnels.
> Contrôle dev v2 et tableaux dans `reports/reprise/demo_dev/` (pas un test
> indépendant). Les trois fichiers gelés requis par les tests ont depuis été
> récupérés avec leurs empreintes exactes. Suite actuelle : **21 réussites,
> 1 xfail, sortie 0**, sans relance des mesures sur les jeux gelés.
> Les sections historiques ci-dessous ne décrivent pas toutes les
> possibilités actuelles de la copie locale.

Ce document dit quels notebooks utiliser, dans quel ordre, ce qu'ils lisent et écrivent,
et ce qui n'est pas encore couvert. Les anciennes versions sont dans `notebooks/` pour
traçabilité ; ne pas les utiliser.

## 1. Notebooks à exécuter (dans cet ordre)

| Ordre | Notebook | Rôle | Entrées | Sorties principales |
|---|---|---|---|---|
| 1 | `notebooks/01_data_exploration.ipynb` | Inventaire du PDF, OCR AR/FR, texte de travail | PDF `data/raw/arabic/majallat_al_shughl_2019.pdf`, pages OCR | `data/processed/texte_travail.json`, `articles_index_draft.csv`, `exploration_summary.json`, `absents_a_verifier.csv`, `verification_sample.csv` |
| 2 | `notebooks/02_segmentation_v15.ipynb` | Découpe en articles, notes de bas de page, corrections vérifiées sur image | `texte_travail.json`, `verification_articles.csv` (rempli à la main, lecture seule) | `articles_ar.csv`, `articles_fr.csv`, `notes_bas_pages.csv`, `segmentation_resume.json` |
| 3 | `notebooks/04_partie_francaise_corrections_v2.ipynb` | Corrections vérifiées sur image dans le texte français | `articles_fr.csv` | `articles_fr_corrige.csv`, `corrections_fr.csv` |
| 4 | `notebooks/03_alignement_fr_ar_v5.ipynb` | Appariement AR/FR par numérotation | `articles_ar.csv`, `articles_fr_corrige.csv` (ou `articles_fr.csv` à défaut) | `alignement_fr_ar.csv`, `alignement_resume.json`, `alignement_echantillon_image.csv` |

Le notebook 04 doit précéder le 03 : le 03 lit `articles_fr_corrige.csv` s'il existe.

Le notebook 01 ne se relance pas à chaque modification : il produit le texte de travail
initial. Les tables de corrections sont dans le notebook 02.

## 2. Résultats de référence (exécution locale du 26 octobre)

- Segmentation AR : 515 articles, 38 abrogés, 20 plages abrogées, 0 identifiant en double, 0 numéro absent sur 1 à 446, 0 article sans chapitre.
- Segmentation FR : 498 entrées, 425 numéros distincts, 1 rupture d'ordre (impression à l'envers, contrôlée).
- Notes de bas de page : 40 lignes dans la table ; 31 notes vérifiées sur image appliquées ; 0 note encore à rattacher.
- Corrections de mots : 104 ; corrections FR vérifiées : 15.
- Alignement : 494 appariées, 21 abrogées (plages), 4 hors Code (loi 66-27, pp. 288–289), 0 absente, 0 doublon, 3 contrôles d'années à relire (AR-335, AR-364, AR-417).

Ces chiffres ne sont pas une évaluation : ils décrivent la cohérence du corpus. Aucun
chiffre d'évaluation sur un test gelé n'existe encore (voir section 4).

## 3. Règles de travail

- Toute correction est vérifiée sur l'image de page avant d'être appliquée (`data/processed/page_images/`).
- Les fichiers remplis à la main (`verification_articles.csv`, `verification_sample_verifie.csv`) ne sont jamais écrasés.
- Une nouvelle version de notebook est créée à chaque modification ; les anciennes ne sont pas supprimées.
- Les résultats sont consignés dans `experiments.md` (une entrée par travail, sans modifier les entrées passées).

## 4. État des composants, jeux et annotations

- Implémenté et lançable : OCR et segmentation (notebooks 01, 02, 04), alignement FR/AR par numérotation (notebook 03), BM25 avec abstention et citation d'extrait (`src/demo/repondre.py`).
- Démo : `python3 src/demo/repondre.py "question"`. Démo complète des scripts d'évaluation : `bash demo_evaluation.sh` (sans mesure sur jeu gelé).
- Tests : `python3 -m pytest` (`tests/test_evaluation.py`). Ils vérifient les sha256 des jeux gelés et le comportement de la démo ; ils ne lancent aucune mesure.
- Jeux gelés (`data/test_locked/`) : alignement v1, OCR v1, questions v1 à v4. Chaque jeu ne se mesure qu'une fois par règle. Les mesures sont consignées dans `experiments.md`.
- Annotations : alignement dev v1 (60 paires, validées par l'auteure), alignement dev v2 (100 paires dictées par l'auteure), rappel (60 articles, en attente), obligations (guide et modèle prêts, annotation en attente). Kappa non calculé : un seul annotateur.
- Non implémenté : obligations par règles, NER par CRF, RAG complet, interface.
- Licence de l'édition IORT : à clarifier avant tout partage (voir `data_card.md`, section 2).
