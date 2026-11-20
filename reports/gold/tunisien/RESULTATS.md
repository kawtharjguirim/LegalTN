# Questions en tunisien (arabizi) — palier Gold (20 novembre 2026)

Commande : `python -X utf8 -m src.tunisien.evaluer --sortie reports/gold/tunisien`
(+ `--modele-traduction qwen2.5:7b --methodes traduction_fr traduction_ar --sortie reports/gold/tunisien/qwen7b`).
Détail par question, traductions comprises : `tunisien_details.csv`.

**Question de recherche du cahier des charges** : la recherche après traduction de la question
bat-elle la recherche multilingue directe pour des questions tunisiennes ?

## Protocole

- **30 questions dans le périmètre, 9 hors périmètre** : 24 + 6 nouvelles (`data/dev/questions_tun_v1.csv`,
  **rédigées par Claude, à valider par une locutrice native**) et les 6 + 3 du dev v2.
  Arabizi réaliste : chiffres (3 = ع, 7 = ح, 9 = ق, 5 = خ) et mots français mêlés.
- Détection automatique du tunisien (`src/tunisien/arabizi.py`) : 100 % des questions tunisiennes
  reconnues, aucune question française ou arabe du dev prise pour du tunisien.
- Cinq méthodes ; abstention avec la règle de la démo, dans la langue du texte effectivement cherché
  (elle n'a pas été réglée pour le tunisien).

## Résultats (30 questions dans le périmètre, 9 hors)

| Méthode | R@1 | R@5 | MRR | Fausse abstention | Répond juste | Hors refusé |
|---|---:|---:|---:|---:|---:|---:|
| A. Directe, corpus français (actuelle) | 0,067 | 0,167 | 0,134 | 0,967 | 0,033 | 1,000 |
| B. **Multilingue directe** (e5, deux corpus) | 0,000 | 0,033 | 0,019 | 0,967 | 0,000 | 1,000 |
| C. Translittération règles → arabe | 0,067 | 0,100 | 0,103 | 1,000 | 0,000 | 1,000 |
| D. **Traduction → français**, qwen2.5:3b | 0,100 | 0,400 | 0,242 | 0,333 | 0,100 | 0,889 |
| E. Traduction → arabe standard, qwen2.5:3b | 0,133 | 0,233 | 0,186 | 0,600 | 0,067 | 0,889 |
| D'. **Traduction → français, qwen2.5:7b** | **0,267** | **0,500** | **0,357** | 0,300 | **0,200** | 0,778 |
| E'. Traduction → arabe standard, qwen2.5:7b | 0,100 | 0,400 | 0,232 | 0,400 | 0,100 | 0,778 |

## Lecture

1. **Réponse à la question de recherche : oui.** Traduire puis chercher bat nettement la recherche
   multilingue directe (R@5 0,40 contre 0,03 avec le même petit modèle). e5 ne comprend pas
   l'arabizi : ses chiffres et sa graphie latine de l'arabe ne ressemblent ni au français ni à l'arabe.
2. **Traduire vers le français vaut mieux que vers l'arabe standard** (R@5 0,40 contre 0,23 avec le
   3B), sans doute parce que les questions mêlent déjà beaucoup de mots français.
3. **La taille du LLM compte** : le 7B multiplie le R@1 par 2,7 (0,10 → 0,27).
4. **Mais le problème n'est pas résolu** : même avec le 7B, une question sur cinq seulement obtient
   une réponse juste. Les traductions sont souvent fausses sur le sens (« Tradouni mel khedma bla
   sbab », renvoyé sans motif → « une absence pour motif personnel » avec le 3B ; « bla sbab »,
   sans motif → « pour un motif » avec le 7B). Les modèles ouverts de 3 à 7 milliards de paramètres
   comprennent mal la derja.
5. **La translittération par règles échoue** : l'arabe obtenu reste du dialecte, loin de la langue
   du Code (« شنوة », « نجم »), et les mots français translittérés n'ont pas d'équivalent.
6. **Risque** : avec la traduction, l'abstention refuse moins bien le hors périmètre (8/9 puis 7/9) :
   une traduction peut rapprocher une question hors sujet du vocabulaire du Code.

## Limites et suite

- Les 24 nouvelles questions sont écrites par Claude, qui n'est pas locuteur natif : **elles doivent
  être relues** (une question qui sonne faux fausse la mesure). Effectif faible (30).
- Pistes : lexique derja → français pour guider la traduction (à construire indépendamment des
  questions d'évaluation) ; modèle spécialisé en dialectes maghrébins ; demander à l'utilisateur de
  confirmer la traduction affichée avant de répondre.
