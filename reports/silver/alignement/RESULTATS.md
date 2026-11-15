# Alignement AR ↔ FR par embeddings — palier Silver (15 novembre 2026)

Commande : `python -X utf8 -m src.alignement_embeddings.evaluer --sortie reports/silver/alignement`
(environnement : `. .\env_silver.ps1`, Python du venv sur D, RTX 2050, fp16).

## Données et protocole

- Corpus : 515 entrées AR (`articles_ar.csv`), 498 entrées FR (`articles_fr_corrige.csv`).
- Gold : **160 paires vérifiées sur image** (dev v1 : 60, dev v2 : 100, disjointes).
- Référence d'accord : 494 couples du pipeline Bronze (numérotation, notebook v6).
- Encodeurs : LaBSE, multilingual-e5-base (préfixe `query:` des deux côtés), 256 tokens.
- Appariement : argmax, meilleurs mutuels, affectation hongroise 1-1.
- Score hybride : `cos(AR, FR) + λ · [même numéro d'article]`, λ ∈ {0 ; 0,1 ; 0,3}.

**Biais à dire en revue** : les paires gold ont été tirées parmi les sorties de la
numérotation puis validées. Le pipeline Bronze y est correct par construction ;
le gold mesure surtout la capacité des embeddings à retrouver ces couples.
Les embeddings étant déterministes à l'inférence, il n'y a pas de variance de graine ici
(les 3 graines s'appliquent au fine-tuning NER).

## Résultats (méthode hongroise)

| Système | Normalisation | λ | P@1 | Précision gold | Rappel gold | Accord avec Bronze (P) |
|---|---|---:|---:|---:|---:|---:|
| Numéro seul, sans suffixe (naïf) | – | – | – | 0,894 | 0,894 | 0,829 |
| LaBSE | brut (en-tête gardé) | 0 | 1,000 | 1,000 | 1,000 | 0,986 |
| LaBSE | **sans en-tête** | 0 | 0,969 | 0,975 | 0,975 | 0,954 |
| LaBSE | sans en-tête + norm. AR | 0 | 0,962 | 0,981 | 0,981 | 0,958 |
| e5-base | **sans en-tête** | 0 | 0,950 | 0,975 | 0,975 | 0,952 |
| e5-base | sans en-tête + norm. AR | 0 | 0,925 | 0,956 | 0,956 | 0,942 |
| LaBSE | sans en-tête | 0,1 | 1,000 | 1,000 | 1,000 | 0,982 |
| e5-base | sans en-tête | 0,1 | 1,000 | 1,000 | 1,000 | 0,986 |

Tableau complet (2 modèles × 3 normalisations × 3 λ × 3 méthodes) : `ablations_alignement.csv`.

## Lecture

1. **L'en-tête numéroté est un raccourci** : avec « Article 14.- / الفصل 14.- », les embeddings
   alignent à 100 % en lisant le numéro. La variante « sans en-tête » mesure le vrai alignement
   sémantique : **97,5 % de précision et de rappel sur le gold**, sans aucune numérotation.
2. **La normalisation orthographique arabe (ablation) n'aide pas** et nuit à e5
   (P@1 0,950 → 0,925) : les encodeurs ont été pré-entraînés sur l'orthographe standard ;
   retirer hamza et ta marbuta crée des formes qu'ils ont peu vues.
3. **Méthode d'appariement** : l'affectation hongroise donne le meilleur équilibre ; les
   meilleurs mutuels sont plus précis (1,000 sur le gold pour LaBSE) mais rappellent moins (0,956).
4. **Hybride (λ = 0,1)** : 100 % sur le gold et 98,2–98,6 % d'accord avec le Bronze. Les
   embeddings départagent les sous-articles de même numéro, que la numérotation seule
   (sans suffixes) confond : 0,894 seulement pour le numéro naïf.

## Analyse d'erreurs (embeddings purs, sans en-tête, hongrois)

Désaccords avec le Bronze : 19 (LaBSE), 20 (e5) ; catégories automatiques à confirmer
dans `desaccords_*.csv` (colonne `categorie`) :

| Catégorie | LaBSE | e5 |
|---|---:|---:|
| Texte vide après en-tête (article abrogé : « (Abrogé par la loi ...) ») | 15 | 16 |
| Abstention (aucun FR libre après affectation 1-1) | 2 | 2 |
| OCR arabe bruité (AR-84) | 1 | 0 |
| À examiner, contenu proche | 1 | 2 |

Les articles abrogés n'ont plus de contenu une fois l'en-tête retiré : leurs embeddings
sont quasi identiques et l'affectation devient arbitraire. C'est la principale limite
des embeddings seuls, et la raison du score hybride.
Cas à examiner pour le palier Gold (divergences AR/FR) : **AR-52** (texte AR sur les
régimes de salaires, FR-52 sur une période transitoire) et **AR-335** (déjà signalé
par le contrôle d'années du Bronze).
