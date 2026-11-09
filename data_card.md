# Carte de données LegalTN — BROUILLON « À VÉRIFIER »

> Brouillon préparé par l'assistant à partir des fichiers du dépôt (9 novembre 2026).
> Tout ce qui est marqué **À VÉRIFIER** doit être confirmé ou corrigé par l'équipe.
> Les chiffres non marqués ont été recomptés sur les fichiers du dépôt.

## 1. Source

| Élément | Valeur |
|---|---|
| Document | Code du travail tunisien, édition bilingue arabe/français — **À VÉRIFIER** : éditeur (IORT ?), année d'édition, numéro d'édition |
| Fichier | `data/raw/arabic/majallat_al_shughl_2019.pdf` |
| Pages | 291 |
| Taille | 1 170 023 octets |
| SHA-256 | `de17529ea734212b6efcec0d796762f39fefbf97455a573ca402bf83c74bc467` |
| Obtention | **À VÉRIFIER** : où et quand le PDF a été obtenu (site, date) |
| Nature | texte de loi publié (pas de données personnelles attendues) — **À VÉRIFIER** |

## 2. Licence et droits

- **À CLARIFIER AVANT TOUT PARTAGE PUBLIC** : le texte de loi lui-même relève en général
  du domaine public, mais la **mise en page, la traduction française et l'édition** peuvent
  appartenir à l'éditeur (IORT ?). Vérifier les conditions de réutilisation.
- Tant que ce point n'est pas réglé : dépôt privé, pas de redistribution du PDF ni des
  images de pages.
- Consentement / anonymisation : sans objet pour un texte de loi — **À VÉRIFIER** que les
  questions de dev et de test ne contiennent aucune donnée personnelle réelle.

## 3. Traitements

1. OCR des 291 pages (notebook `01_data_exploration.ipynb`, Tesseract ; caches dans
   `data/processed/ocr_pages*/` et `ocr_bandes/`).
2. Segmentation en articles et corrections vérifiées sur image (notebooks 02 et 04,
   **non présents dans le dépôt**).
3. Alignement AR/FR par numérotation (`notebooks/03_alignement_fr_ar_v6.ipynb`).

## 4. Tailles par langue

| Corpus | Fichier | Lignes | Indexé pour la recherche |
|---|---|---:|---:|
| Arabe | `data/processed/articles_ar.csv` | 515 entrées (38 abrogées, 20 plages) | 491 lignes, 441 intitulés distincts |
| Français | `data/processed/articles_fr_corrige.csv` | 498 entrées (identifiants non uniques) | 496 lignes, 439 intitulés distincts |
| Alignement | `data/processed/alignement_fr_ar_v6.csv` | 519 lignes : 494 appariées, 21 abrogées (plage), 4 hors Code | — |

## 5. Jeux d'évaluation

| Jeu | Fichier | Taille | Statut |
|---|---|---:|---|
| Questions dev v2 | `data/dev/questions_dev_v2.csv` | 56 (FR 44, tunisien 9, AR 3 ; 27 dans / 29 hors périmètre) | développement, déjà consulté |
| Alignement dev | `data/dev/alignement_dev_v1.csv`, `alignement_dev_v2_a_annoter.csv` | 60 + 100 paires | validées par l'auteure |
| Questions test v2 | `data/test_locked/questions_reference_v2.csv` | 40 | gelé, SHA-256 vérifié par les tests |
| OCR test | `data/test_locked/ocr_candidats_v1.csv`, `ocr_baseline_v1.csv` | 30 + 30 | gelé ; gold OCR absent |
| Obligations test | `data/test_locked/obligations_candidats_test_v1.csv` | 100 | gelé, non annoté |
| Annotations à faire | voir `rapport_etape.md` | — | obligations, NER, rappel d'alignement : 0 ligne annotée |

**À VÉRIFIER** : date et commit du gel de chaque jeu de test (le dépôt Git a été créé
après coup, le 28 octobre 2026 ; les empreintes sont consignées dans `experiments.md`).

## 6. Annotation

- Guides : `data/dev/obligations_guide_annotation_v1.md`, `data/dev/ner_guide_annotation_v1.md`.
- Annotateurs : **À VÉRIFIER** (un seul à ce jour) ; kappa non calculé.
  Script prêt : `src/evaluation/calculer_kappa.py`.

## 7. Limites connues

- Pas de question arabe dans le périmètre du dev : rappel arabe non mesurable.
- Erreurs d'OCR résiduelles possibles ; notebooks de segmentation et de correction absents.
- 69 étiquettes françaises sans suffixe dans l'alignement ; 17 paires « apparié » dont
  l'article arabe porte `abroge=True`.
