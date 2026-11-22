# Gold — Question de recherche

**La citation obligatoire réduit-elle les hallucinations sans augmenter les refus injustifiés ?**

Source : sorties RAG déjà mesurées (`reports/silver/rag_dev/resultats.json`, dev v2, qwen2.5:3b, température 0, graine 2026, 54 questions dont 26 dans le périmètre et 28 hors périmètre ; D01 et D14 exclues car exemples few-shot). Aucun nouvel appel au LLM. Script : `src/evaluation/question_recherche.py`. Bootstrap apparié, 10 000 tirages, graine 2026.

## Définitions (par question)

- **Réponse non fondée** : le système répond (pas d'abstention) alors que la question est hors périmètre, ou alors qu'elle est dans le périmètre sans citer l'article de référence.
- **Refus injustifié** : abstention sur une question dans le périmètre.

## Variantes

| Variante | Description | Réponses non fondées /54 | Refus injustifiés /26 |
|---|---|---|---|
| P0 | LLM seul, sans passages | 54 | 0 |
| P1 | RAG libre (passages, pas de format imposé) | 34 | 0 |
| P2 | RAG + JSON + citation obligatoire + règle d'abstention | 8 | 2 |
| P3 | P2 + exemples few-shot | 12 | 1 |
| P2V | P2 + vérification des citations | 7 | 3 |

## Comparaisons appariées (IC 95 % sur la différence de taux)

| Comparaison | Δ non fondées | IC 95 % | Δ refus injustifiés | IC 95 % |
|---|---|---|---|---|
| P2 vs P1 | −26 | [−63 %, −35 %] | +2 | [0 %, +19 %] |
| P2V vs P1 | −27 | [−63 %, −37 %] | +3 | [0 %, +23 %] |
| P2V vs P0 | −47 | [−94 %, −78 %] | +3 | [0 %, +23 %] |

## Réponse (provisoire, dev)

- **Oui pour les hallucinations** : la citation obligatoire avec règle d'abstention divise par environ 5 les réponses non fondées par rapport au RAG libre (34 → 7), et l'intervalle exclut zéro.
- **Pas tout à fait pour les refus** : les refus injustifiés passent de 0 à 2 (P2) ou 3 (P2V) sur 26. L'intervalle touche 0, donc l'augmentation n'est pas significative sur ce petit échantillon, mais elle existe et doit être dite.
- La vérification P2V gagne 1 réponse non fondée de moins que P2, au prix d'1 refus injustifié de plus.

## Limites

- Dev uniquement (déjà utilisé pour concevoir les prompts) : résultat indicatif, pas une preuve.
- Petits effectifs : 26 dans le périmètre, dont 6 en tunisien et **0 en arabe** ; la question n'est pas encore répondue par langue.
- Un seul modèle (qwen2.5:3b) et une seule graine de génération (température 0).
- « Non fondée » est une mesure automatique par l'article cité, pas un jugement humain de fidélité : le LLM-juge validé et l'annotation humaine restent à faire.
