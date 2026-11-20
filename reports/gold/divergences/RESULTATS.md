# Divergences AR / FR — palier Gold (20 novembre 2026)

Commandes : `python -X utf8 -m src.divergences.detecter` puis
`python -X utf8 -m src.divergences.evaluer --jugements data/a_annoter/divergences_jugements_claude_v1.json`.

## Détection

Sur les **478 paires** d'articles alignés non abrogés (494 moins les articles vides), trois signaux
calculés sur le contenu, sans intitulé numéroté ni mention « Modifié par la loi… » :
- **similarité LaBSE** (médiane 0,875, minimum 0,113) ;
- **nombres différents** (chiffres et nombres en lettres FR/AR, duels arabes, hors « 1 ») : 123 paires ;
- écart de longueur FR/AR à la médiane.

Classement complet : `paires_scores.csv`.

## Évaluation sur un échantillon jugé

34 paires (`data/a_annoter/divergences_echantillon_v1.csv`) : 12 plus faibles similarités, 12 plus
forts écarts de nombres, 10 **témoins tirés au hasard** (graine fixe). Jugements **par Claude,
statut `verifie_claude`, à relire** (`divergences_jugements_claude_v1.json`).

| Sélection | n | Même sens | Défaut d'OCR | Défaut de segmentation | Divergence réelle | Part de problèmes |
|---|---:|---:|---:|---:|---:|---:|
| Similarité faible | 12 | 1 | 7 | 4 | 0 | **0,917** |
| Nombres différents | 12 | 3 | 9 | 0 | 0 | **0,750** |
| Témoins aléatoires | 10 | 10 | 0 | 0 | 0 | 0,000 |

## Lecture

1. **Le détecteur repère très bien les paires à problème** (92 % et 75 % contre 0 % au hasard),
   mais ce qu'il trouve, ce sont surtout des **défauts du texte numérisé**, pas des différences de
   la loi : **aucune divergence juridique réelle** dans l'échantillon.
2. **8 paires ont un défaut qui change une règle dans la version arabe** (colonne
   `impact_juridique`), par exemple :
   - **congé de maternité (art. 64)** : « مدة 0 يوما » et « 5 يوما » pour **30** et **15** jours ;
   - **heures supplémentaires (art. 90)** : « 29675 », « 9050 » pour **75 %, 25 %, 50 %** ;
   - **amende (art. 425)** : « 2858 » pour **288** dinars ; **résiliation (art. 351)** : délai de
     **3 mois** absent ; **sanctions (art. 234, 94-14)** : listes ou renvois incomplets.
   LegalTN cite ces extraits arabes tels quels : une réponse en arabe sur le congé de maternité
   afficherait un chiffre faux. **Correction prioritaire du corpus arabe** (vérification sur image,
   comme au Bronze).
3. **AR-52**, signalé comme divergence possible au Silver, a **le même sens** : le français ajoute
   une note de bas de page et des intitulés. **AR-335** reste à vérifier : la ligne française
   alignée n'est qu'un intitulé, le contenu de l'article 335 manque côté français.
4. Taux de vraies divergences dans le Code : **0 sur 10 témoins** — faible, mais 10 paires ne
   suffisent pas à l'estimer précisément (intervalle de confiance à 95 % : 0 à 31 %).

## Limites

- Jugements par Claude, à relire ; échantillon de 34 paires.
- Le convertisseur de nombres additionne deux nombres arabes coordonnés (« ستة عشر وثمانية عشر » lu
  34) : faux écarts possibles.
- Suite : faire juger par un humain les 123 paires à écart de nombres, en priorité celles des
  articles cités par la démo ; corriger les chiffres arabes sur image.
