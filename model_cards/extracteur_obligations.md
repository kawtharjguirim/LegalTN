# Carte de modèle — Extracteur d'obligations par règles — BROUILLON « À VÉRIFIER »

> Brouillon préparé par l'assistant (9 novembre 2026).

| Élément | Valeur |
|---|---|
| Code | `src/obligation_extraction/extraire_obligations.py`, `evaluer_obligations.py` |
| Type | règles (expressions régulières), pas d'apprentissage |
| Règles | marqueurs modaux en trois classes (`obligation`, `interdiction`, `permission`) ; rôle `qui` avant le marqueur ; action `quoi` après ; condition `quand` si le texte la précise ; exclusion des définitions |
| Référence | guide `data/dev/obligations_guide_annotation_v1.md` |
| Entrée | phrases candidates du texte français |
| Sortie | prédictions `est_obligation_predite, modal_predit, qui_predit, quoi_predit, quand_predit` |

## Résultats

- Sur les 200 candidats du dev (`data/dev/obligations_predictions_dev_v1.csv`) :
  178 phrases classées obligations (113 `obligation`, 59 `interdiction`, 6 `permission`),
  22 non-obligations.
- **Aucune précision, rappel ou F1 mesurés** : le gold est vide (0/200 dev, 0/100 test).
  L'évaluateur refuse de calculer sans annotation.

## Limites

- Les classes prédites n'ont pas été vérifiées par un humain.
- **À FAIRE** : annoter le dev, régler les règles sur le dev, puis mesurer une seule fois
  le F1 par rôle sur les 100 phrases du test gelé, contre une baseline triviale
  (par exemple « toujours `obligation` »).
