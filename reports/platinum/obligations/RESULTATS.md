# Extracteur d'obligations — évaluation sur le dev (21 novembre 2026)

Commande : `python -X utf8 -m src.obligation_extraction.evaluer_obligations --gold data/a_annoter/obligations_dev_claude_v1.csv --predictions data/dev/obligations_predictions_dev_v1.csv --sortie reports/platinum/obligations/evaluation_dev_extracteur.json --erreurs reports/platinum/obligations/erreurs_dev_extracteur.csv`

**Gold = pré-annotation de Claude (`verifie_claude`), non relue par un humain. Dev seulement : le test
n'est pas mesuré** (il ne se mesure qu'une fois, après relecture). Le dev a été annoté avec les
prédictions de l'extracteur sous les yeux : accord probablement surestimé.

## Détection et type (200 phrases)

| | Précision | Rappel | F1 |
|---|---:|---:|---:|
| Obligation vs non-obligation | 0,921 | 0,959 | 0,940 |
| Modal : obligation (107) | 0,991 | 0,981 | 0,986 |
| Modal : interdiction (53) | 0,981 | 0,981 | 0,981 |
| Modal : permission (4) | 0,800 | 1,000 | 0,889 (4 cas seulement) |

## F1 par rôle (nouveau)

Le rôle (`qui`) est ramené à une **classe** (employeur, salarié, apprenti, maître, administration,
juridiction, organisation, parties, toute personne, autre, **aucun** = rôle non nommé) par
`classe_role` : « Tout employeur qui fait une avance » et « les employeurs » sont tous deux
`employeur`. Évalué sur les 164 phrases retenues comme obligations par l'annotation et par l'extracteur.

| Classe | Support (gold) | Précision | Rappel | F1 |
|---|---:|---:|---:|---:|
| aucun (rôle non nommé) | 101 | 0,700 | 0,762 | 0,730 |
| employeur | 26 | 0,571 | 0,462 | 0,511 |
| salarié | 9 | 0,333 | 0,556 | 0,417 |
| administration | 7 | 0,667 | 0,286 | 0,400 |
| juridiction | 3 | 1,000 | 0,667 | 0,800 |
| maître | 4 | 1,000 | 0,500 | 0,667 |
| organisation | 5 | 0,200 | 0,200 | 0,200 |
| apprenti, parties, toute personne | 1 chacune | 0 | 0 | 0 |
| autre | 6 | – | 0 | 0 |

**Exactitude des classes de rôle : 0,616. F1 macro : 0,339** (0,299 en ne comptant que les rôles
nommés). Lecture : l'extracteur trouve le type d'obligation presque toujours, mais **le rôle
rarement** : dans 101 phrases sur 164 le rôle n'est pas nommé (voix passive, sujet « il »). Parmi
elles, l'extracteur attribue quand même un rôle dans 24 cas, et inversement il ne trouve aucun rôle
dans 33 phrases où l'annotation en nomme un. Plusieurs classes ont moins de 10 exemples : leurs F1
sont indicatifs.

Tests : `tests/test_obligations.py` (`classe_role`, `f1_par_role`).
