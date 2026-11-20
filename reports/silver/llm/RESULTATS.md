# LLM et prompting — palier Silver (15 novembre 2026)

Commande : `python -X utf8 -m src.rag.evaluer_llm --sortie reports/silver/llm`
Modèle : **qwen2.5:3b** (Ollama, Q4_K_M, local, RTX 2050), température 0.

## Protocole

- 77 questions de dev : `questions_dev_v2.csv` (21 FR + 6 tunisien dans le périmètre,
  29 hors périmètre) et 21 traductions AR (**faites par Claude, à valider**). Aucun test gelé.
- Contexte : 3 premiers articles de la recherche hybride BM25 + e5. Le LLM est évalué **sans** le
  filtre d'abstention de la recherche, pour mesurer son propre comportement, y compris face à un
  contexte hors sujet ; les colonnes « pipeline » ajoutent le seuil par langue de la démo.
- Stratégies : `zero_shot` (consignes) ; `few_shot` (+ 2 exemples FR/AR) ; `citation_forcee`
  (few-shot + vérification : une réponse sans citation `[Article N]` valide, ou citant un article
  absent du contexte, est remplacée par l'abstention).
- Température 0, **une seule exécution par stratégie**. Correction du 16 novembre : ce décodage
  **n'est pas déterministe** d'une exécution à l'autre (calculs GPU, cache de prompts d'Ollama).
  Sur la question du congé fractionné, trois exécutions ont donné « oui », « non » puis une
  abstention ; les questions de la démo, elles, ont donné 3/3 réponses identiques. Les chiffres
  ci-dessous ont donc une variance non mesurée : répéter l'évaluation pour l'estimer.

## Résultats (global, 48 questions dans le périmètre, 29 hors)

| Stratégie | Référence citée | Format `[Article N]` | Citation inventée | Abstention à tort | Hors périmètre refusées | Langue respectée | Latence |
|---|---:|---:|---:|---:|---:|---:|---:|
| zero_shot | 0,542 | 0,833 | 0,028 | 0,250 | **1,000** | 1,000 | 1,1 s |
| few_shot | 0,625 | 0,864 | 0,023 | **0,083** | 0,931 | 1,000 | 1,2 s |
| **citation_forcee** | **0,667** | **1,000** | **0,000** | 0,167 | 0,931 | 1,000 | 1,1 s |

Plafond : la référence n'est dans les 3 articles transmis que pour **0,812** des questions
(FR 1,000 ; AR traduites 0,857 ; tunisien 0,000). « Référence citée » ne peut pas dépasser ce plafond.

Par langue, `citation_forcee` : FR 0,857 de références citées ; AR traduites 0,667 ; tunisien 0,000
(la recherche ne trouve jamais l'article en arabizi). Avec le seuil de la démo, **100 % des
questions hors périmètre sont refusées** pour les trois stratégies.

Détail par question : `prompting_details.csv` ; agrégats par langue : `prompting_resultats.json`.

## Lecture

1. **La citation forcée supprime les citations inventées** (0,028 → 0,000) et garantit le format,
   au prix de fausses abstentions (0,083 → 0,167 par rapport au few-shot) : réponses rejetées faute
   de citation au bon format. C'est la question de recherche du cahier des charges (« la citation
   obligatoire réduit-elle les hallucinations sans augmenter les refus injustifiés ? ») : **oui pour
   les hallucinations de citation, mais elle augmente les refus**.
2. **Le few-shot est le meilleur compromis pour répondre** : le moins d'abstentions à tort (0,083).
   En zero-shot, le modèle mentionne souvent « l'article 79 » en texte libre au lieu du format
   demandé, et refuse plus souvent (0,250).
3. **Le LLM seul refuse bien le hors-périmètre** (0,93 à 1,00) même quand on lui fournit un
   contexte sans rapport ; avec le seuil de recherche, 100 %.
4. **Une citation correcte ne garantit pas une réponse fidèle.** Exemple observé dans la démo le
   15 novembre : « Un congé payé de cinq jours ouvrables peut-il être fractionné ? » → le LLM cite
   l'article 118 (correct) mais répond « oui », alors que l'article impose un congé continu en
   dessous de six jours (réponse non reproduite à l'identique le 16 : voir la correction plus haut). Ces métriques automatiques mesurent la citation, pas la fidélité du contenu : à évaluer
   à la main ou par LLM-juge (palier Gold).

## Résumés en langage clair

40 résumés (20 articles FR, 20 AR, les articles de référence du dev), latence ≈ 2 à 3 s :
`resumes_a_noter.csv`, **colonnes `exactitude_1_5` et `clarte_1_5` à remplir à la main**
(grille humaine demandée par le cahier des charges).
