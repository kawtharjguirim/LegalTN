# Gold — Audit des hallucinations et de l'abstention par langue (dev v2)

Source : `reports/silver/rag_dev/resultats.json` (5 variantes, qwen2.5:3b, température 0). Aucun nouvel appel LLM.
« Citations inventées » = articles cités qui n'étaient pas dans les passages fournis.

| Langue | Variante | Citations inventées | Bon article cité | Hors périmètre refusé | Fausses abstentions |
|---|---|---|---|---|---|
| FR | P0 | 31 | 0/20 | 0/22 | 0/20 |
| FR | P1 | 0 | 18/20 | 0/22 | 0/20 |
| FR | P2 | 0 | 16/20 | 21/22 | 2/20 |
| FR | P3 | 1 | 17/20 | 18/22 | 1/20 |
| FR | P2V | 0 | 16/20 | 21/22 | 3/20 |
| Tunisien | P0 | 6 | 0/6 | 0/3 | 0/6 |
| Tunisien | P1 | 0 | 2/6 | 0/3 | 0/6 |
| Tunisien | P2 | 0 | 2/6 | 2/3 | 0/6 |
| Tunisien | P3 | 2 | 2/6 | 1/3 | 0/6 |
| Tunisien | P2V | 0 | 2/6 | 2/3 | 0/6 |
| Arabe | toutes | 0 | — (0 question) | P0 / P1 : 0/3 ; P2 / P3 / P2V : 3/3 | — |

## Lecture

- **Hallucination de citation** : le LLM seul (P0) invente des articles (37 au total) ; dès qu'il reçoit des passages, il n'en invente presque plus (P3 few-shot : 3), et la vérification P2V garantit 0.
- **Écart entre langues** : bon article cité FR 16/20 (80 %) contre tunisien 2/6 (33 %) en P2V. L'écart vient surtout de la recherche BM25 sur l'arabizi (R@5 BM25 tunisien 3/6), pas du LLM.
- **Arabe** : non mesurable, aucune question arabe dans le périmètre du dev. Les questions sont en cours d'écriture par l'équipe (base Notion « Questions Gold »).

## Limites

Dev non indépendant ; effectifs tunisien et arabe très petits (6 et 3) ; variabilité d'Ollama d'environ une question d'une exécution à l'autre (voir experiments.md, 22 nov.).
