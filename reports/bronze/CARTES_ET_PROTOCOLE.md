# LegalTN — Cartes et protocole (revue Bronze)

État au 27-28 octobre 2026. Ce document regroupe la carte de données, la
carte du système, la carte de modèle, le protocole d'évaluation et les
limites connues. Tout chiffre présenté doit être retrouvable dans
`experiments.md`.

## 1. Carte de données

| Élément | Détail |
|---|---|
| Source | Code du travail tunisien, PDF `data/raw/arabic/majallat_al_shughl_2019.pdf` (291 pages, édition bilingue AR/FR), SHA-256 consigné dans `experiments.md` |
| Corpus arabe | `data/processed/articles_ar.csv` — 515 entrées, `77fe24b3…46022` |
| Corpus français | `data/processed/articles_fr.csv` — 498 entrées, `a75e4c21…a122b` |
| Corpus FR corrigé | `data/processed/articles_fr_corrige.csv` — 498 entrées, 34 textes corrigés, `ac627cfc…8e071` |
| Dev retrieval | `data/dev/questions_dev_v2.csv` — 56 questions (27 dans / 29 hors périmètre ; 44 FR, 9 tunisien, 3 AR), `9c616a6c…59deb8` |
| Dev alignement | `alignement_dev_v1.csv` (60) + `alignement_dev_v2_a_annoter.csv` (100) — contrôles déjà consultés |
| Dev obligations | `obligations_candidats_dev_v1.csv` — 200 phrases candidates, annotations vides |
| Test gelé | `data/test_locked/` : `questions_reference_v2.csv` (40), `ocr_candidats_v1.csv` (30), `ocr_baseline_v1.csv` (30), `obligations_candidats_test_v1.csv` (100 candidates, champs vides). Empreintes dans `tests/test_evaluation.py` et `recuperation_jeux_geles.json` |
| Annotation | Un seul annotateur (l'auteure) : kappa inter-annotateurs non calculable — à dire en revue |

## 2. Carte du système

| Composant | Implémentation | Entrées | Sorties |
|---|---|---|---|
| Alignement AR/FR | Règles par numérotation + suffixes (`notebooks/03_alignement_fr_ar_v6.ipynb`, exécutable via `src/executer_alignement.py`) | `articles_ar.csv`, `articles_fr_corrige.csv` | `alignement_fr_ar.csv`, `alignement_resume.json`, `alignement_echantillon_image.csv` |
| Extraction d'obligations | Règles FR : modaux, rôles, conditions (`src/obligation_extraction/extraire_obligations.py`) | phrases candidates | `obligations_predictions_dev_v1.csv` (prédictions, pas un gold) |
| NER | CRF (`src/ner_crf/`, sklearn-crfsuite, traits orthographiques + contexte ±2) | phrases étiquetées BIO | spans PER/ORG/LOC/MISC ; schéma légal `ner_guide_annotation_v1.md` |
| Retrieval / démo | BM25 k1=1.5 b=0.75 (`src/evaluation/baseline_bm25.py`) + `src/demo/repondre.py` | question FR/AR | article cité + extrait + page, ou abstention (seuil 9,085, inchangé) |
| API de démo | `api.py` HTTP local `GET /health`, `POST /repondre` ; `demarrer.ps1` | JSON | JSON |

## 3. Carte de modèle

| Modèle | Type | Configuration | Usage |
|---|---|---|---|
| CRF NER | linéaire, L-BFGS, c1=c2=0.1, ≤100 itérations | traits : mot, suffixes, casse, chiffres, POS si disponible, fenêtre ±2 | validé sur CoNLL-2002 ; gold LegalTN à annoter |
| BM25 | retrieval lexical | k1=1.5, b=0.75, IDF style Lucene, normalisation FR/AR dédiée | démo et baseline de rappel |
| Extracteur d'obligations | règles déterministes | listes de marqueurs modaux/roles/conditions figées | candidats annotables, à mesurer sur gold humain |

## 4. Protocole d'évaluation

- **Séparation** : dev = lots A/B alignement, questions_dev_v2, 200 candidats
  obligations ; test gelé = `data/test_locked/` (questions 40, OCR 30,
  obligations 100 candidates). Le seuil de démo (9,085) date de l'historique
  et n'a pas été réglé sur le test ni pendant cette reprise.
- **Gel** : empreintes SHA-256 des jeux gelés consignées dans
  `experiments.md` et vérifiées par `tests/test_evaluation.py`.
- **Résultats publiés reproduits** : baseline CoNLL-2002 (Tjong Kim Sang
  2002, Table 1) — voir `reports/reprise/conll2002_reproduction.json`.
- **Reproductibilité** : commandes dans `README.md` et `PIPELINE.md` ;
  environnement `.venv` (`requirements-alignement.txt` + deps NER).

## 5. Mesures disponibles vs validations manquantes

| Composant | Mesuré | Non mesuré (en attente) |
|---|---|---|
| Alignement AR/FR | 494 appariements, 0 doublon, concordance sur 160 références dev | P/R/F1 sur gold indépendant (lot `rappel_alignement_a_annoter_v1.csv` à remplir) |
| Retrieval BM25 | R@1=21/27, R@5=23/27 (dev, sans seuil) ; seuil : 27/29 refus hors périmètre, 4 fausses abstentions | mesure unique sur test gelé (déjà consommé historiquement) |
| Obligations | 178/200 candidats classés obligation par les règles | F1 par rôle : nécessite annotations dev + test |
| NER CRF | reproduction CoNLL-2002 (voir rapport) | F1 spans sur corpus légal : nécessite `ner_a_annoter_v1.csv` rempli |
| OCR | pipeline existant, caches récupérés | gold `ocr_gold_v1.csv` absent → P/R caractères non calculables |
