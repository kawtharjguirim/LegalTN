# LegalTN

Assistant de recherche dans le Code du travail tunisien bilingue arabe/français
(édition IORT, PDF de 291 pages). Une question en français, en arabe, en tunisien
ou en arabizi renvoie l'article cité (numéro, page, extrait), ou une abstention
si la question sort du Code. **Composants classiques uniquement** : règles,
lexiques, SymSpell, BM25. Aucun LLM, aucun modèle neuronal, aucune API payante.

## Installer et lancer (une commande)

Prérequis : Windows, **Python 3.11 ou plus** dans le `PATH` (vérifié avec 3.11.9).

```powershell
.\demarrer.ps1
```

Le script crée `.venv` s'il manque (ou s'il est inutilisable), installe
`requirements.txt`, puis lance l'API et l'interface web sur
**http://127.0.0.1:8000** (port modifiable : `.\demarrer.ps1 -Port 18765`).
Le serveur écoute uniquement en local.

## Utiliser

- **Interface web** : http://127.0.0.1:8000. Le bandeau « Vouliez-vous dire : … ? »
  apparaît si la question a été corrigée, et le bouton « Voir les étapes » montre
  la question après chaque étape du pipeline.
- **Ligne de commande** :
  `.venv\Scripts\python -X utf8 src/demo/repondre.py --debug "Quel est le préavis pour un CDI ?"`
- **API** : `GET /health` ; `POST /repondre` avec `{"question": "...", "k": 3}`
  (`k` entre 1 et 5). La réponse contient `question_originale`, `question_corrigee`,
  `corrections`, `langue_detectee`, `etapes`, `abstention`, `candidats`
  (article, page, texte, score) et `latence_ms`.

## Pipeline de traitement des questions

`src/pipeline/traitement.py`, une fonction testable par étape :

1. détection de langue (fr, ar, tunisien, arabizi) ;
2. translittération arabizi → arabe (mots français connus et nombres gardés) ;
3. mots vides (`data/lexiques/stopwords_fr.txt`, `stopwords_ar.txt`), retirés avant la
   normalisation de ى ; les négations et les modaux ne sont jamais retirés ;
4. normalisation (FR : minuscules, accents ; AR : أإآ→ا, ة→ه, ى→ي, diacritiques, tatweel) ;
5. lexique tunisien → standard et sigles (CDI, CDD, SMIG, SMAG, CNSS) ;
6. racinisation arabe légère (reste ≥ 3 lettres) ;
7. correction orthographique SymSpell (`src/correction/`) ;
8. synonymes juridiques (expansion) ;
9. BM25 (k1 = 1,5, b = 0,75), abstention sous le seuil 9,085.

`data/dev/lexique_tunisien_v1.csv` et `data/dev/synonymes_juridiques_v1.csv` sont
des **modèles de 5 exemples à valider**.

## Tests

```powershell
.venv\Scripts\python -m pytest -q -p no:cacheprovider
```

Dernier résultat : **72 réussis, 1 xfail, 0 échec**. Le xfail strict documente
une limite volontairement conservée du BM25 historique seul (sigle « CDI ») ;
le pipeline complet répond sur ce cas. Les tests ne lancent aucune mesure sur
les jeux gelés : ils vérifient leurs SHA-256.

## Chiffres de référence

| Élément | Valeur |
|---|---|
| Corpus | 515 entrées AR, 498 entrées FR (`data/processed/`) |
| Index de recherche | 496 articles FR, 491 AR (intitulés reconnus) |
| Alignement AR/FR | 494 appariés, 21 abrogés (plage), 4 hors Code, 6 contrôles d'années |
| Dev v2 (`data/dev/questions_dev_v2.csv`) | 56 questions : 27 dans le périmètre, 29 hors |
| Jeux gelés (`data/test_locked/`) | 40 questions, 30 OCR, 30 baseline OCR, 100 obligations |

Résultats sur le dev (non indépendant) et ablation du pipeline : voir
[`experiments.md`](experiments.md). Aucun résultat sur test gelé n'est publié ici.

## Reproduire

| Commande | Sortie |
|---|---|
| `python src/executer_alignement.py --sortie reports/mon_alignement` | alignement AR/FR |
| `python -X utf8 src/evaluation/evaluer_pipeline_dev.py --rapports reports/mon_pipeline` | ablation du pipeline (dev) |
| `python -X utf8 src/evaluation/evaluer_correction_dev.py --rapports reports/ma_correction` | effet de SymSpell (dev) |
| `python -m src.ner_crf.reproduire_baseline_conll` | reproduction CoNLL-2002 (CRF, baseline publiée) |

Les scripts refusent d'écrire dans un dossier existant non vide : choisir un dossier neuf.

## Limites connues

- Pas de question arabe dans le périmètre du dev : le rappel arabe n'est pas mesuré.
- Arabizi : la translittération évite les abstentions à tort mais ne retrouve pas
  le bon article et accepte des questions hors périmètre (`reports/erreurs_analysees_dev.csv`).
- Le seuil 9,085 a été choisi pour le BM25 historique ; il sera réglé une seule fois
  sur le pipeline final, sur le dev.
- Annotations humaines (obligations, NER, rappel d'alignement) encore vides.
- Licence de l'édition IORT à clarifier avant tout partage public.

Historique de la reprise du projet : [`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md) et
[`PIPELINE.md`](PIPELINE.md).
