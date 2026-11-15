# Recherche dense bilingue — palier Silver (15 novembre 2026)

Commande : `python -X utf8 -m src.rag.evaluer --sortie reports/silver/rag`

## Protocole

- Questions : `questions_dev_v2.csv` (21 FR + 6 tunisien dans le périmètre, 29 hors périmètre
  dont 3 AR) et `questions_dev_ar_traduites_v1.csv` (21 traductions AR des questions FR,
  **faites par Claude, à valider**). 77 questions ; aucun test gelé lu.
- Index : articles FR (`articles_fr_corrige.csv`) et AR (`articles_ar.csv`), mêmes lignes que la
  démo Bronze. Intitulé (« 14 bis ») = clé commune aux deux langues.
- Systèmes : BM25 Bronze ; dense (e5-base avec préfixes `query:`/`passage:`, LaBSE) ;
  hybride = fusion RRF (k = 60) de BM25 et dense ; « bilingue » = interroger aussi le corpus de
  l'autre langue (dense seulement, BM25 étant lexical).
- Abstention : BM25 garde la règle Bronze (score < 9,085, réglée historiquement sur ce dev :
  résultat optimiste). Dense : seuil sur le meilleur cosinus, **réglé en leave-one-out**, global
  ou par écriture (arabe, français, tunisien latin).

**Limite** : dev déjà consulté pendant le Bronze, 77 questions seulement ; écart de 1 question
= 4,8 points en FR. Ces chiffres orientent les choix, ils ne sont pas un résultat final.

## Résultats principaux

| Configuration | R@1 FR | R@1 AR (trad.) | R@1 tunisien | R@5 global | Abst. à tort (/48) | Hors refusées (/29) | Exactitude bout en bout |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 (Bronze, seuil 9,085) | 0,95 | 0,52 | 0,17 | 0,83 | 7 | 27 | 0,766 |
| Dense e5, seuil global | 1,00 | 0,48 | 0,00 | 0,83 | 21 | 22 | 0,597 |
| Dense e5, seuil par langue | 1,00 | 0,48 | 0,00 | 0,83 | 3 | 24 | 0,701 |
| **Hybride e5, seuil par langue** | **1,00** | **0,62** | 0,00 | 0,83 | **3** | 24 | 0,753 |
| Hybride e5 bilingue, seuil par langue | 0,71 | 0,62 | 0,00 | 0,79 | 3 | 24 | 0,662 |
| Hybride LaBSE, seuil par langue | 0,71 | 0,57 | 0,17 | 0,81 | 7 | 24 | 0,649 |

Tableau complet (18 configurations, métriques par langue) : `ablations_rag.csv` ;
classement de chaque question : `details_rag.csv`.

## Lecture

1. **e5 > LaBSE pour la recherche** : LaBSE est entraîné à repérer des traductions (excellent pour
   l'alignement), pas à associer une question à un passage. Dense LaBSE seul : R@1 FR 0,33.
2. **L'hybride RRF est le meilleur compromis** : il garde 1,00 en FR et gagne 10 points en
   arabe sur BM25 (0,62 contre 0,52).
3. **Le seuil d'abstention doit dépendre de la langue** : les cosinus e5 ne sont pas sur la même
   échelle (FR dans le périmètre 0,86–0,91 ; AR 0,78–0,87). Un seuil global rejette presque
   toutes les questions AR et tunisiennes valides (21 fausses abstentions) ; par langue : 3.
4. **Le mode bilingue dégrade le FR** (1,00 → 0,71) : fusionner les classements des deux corpus
   ajoute du bruit quand la question est déjà dans la langue de l'article. Pour une citation
   bilingue, mieux vaut chercher dans la langue de la question puis afficher l'article
   correspondant de l'autre langue via l'alignement.
5. **Le tunisien en écriture latine reste non résolu** (0/6 en dense) : aucun encodeur testé ne
   comprend l'arabizi (« 7 », « 3 », « 9 »). Piste Gold : translittération vers l'arabe avant
   la recherche, ou traduction par le LLM.
