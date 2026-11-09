# Carte de modèle — Correction orthographique SymSpell — BROUILLON « À VÉRIFIER »

> Brouillon préparé par l'assistant (9 novembre 2026). Chiffres repris de `experiments.md`.

| Élément | Valeur |
|---|---|
| Code | `src/correction/correcteur_symspell.py` ; étape 7 de `src/pipeline/traitement.py` |
| Type | distance d'édition (Damerau-Levenshtein) sur un dictionnaire, pas d'apprentissage |
| Bibliothèques | symspellpy 6.10.2 (MIT) ; pyspellchecker 0.9.1 (MIT), lexique général utilisé **seulement** pour ne pas corriger un mot connu |
| Dictionnaires | mots du corpus avec leur fréquence réelle : 3 654 mots FR, 6 227 formes AR (3 373 réduites) ; mots vides exclus dans le pipeline |
| Distance max | 1 pour les mots de 4 lettres ou moins, 2 au-delà |
| Jamais corrigés | nombres, mots de moins de 3 lettres, mots connus, noms propres (majuscule hors début de phrase), questions arabizi |
| Avant SymSpell | lexique de sigles : CDI, CDD, SMIG, SMAG, CNSS |

## Résultats (dev v2, fautes synthétiques, graine 2026)

| Condition | R@1 | R@5 | Refus hors périmètre |
|---|---|---|---|
| questions propres, sans correction | 21/27 | 21/27 | 27/29 |
| questions propres, avec correction | 21/27 | 21/27 | 26/29 |
| avec fautes, sans correction | 19/27 | 20/27 | 29/29 |
| avec fautes, avec correction | 21/27 | 21/27 | 25/29 |

## Limites

- Fautes **synthétiques** : à remesurer sur des fautes réelles (`rapport_etape.md`, point 4).
- Fausse correction observée : « loyor » → « loger » (D17) ; plus de questions hors
  périmètre acceptées une fois corrigées.
- Aucune mesure sur test gelé.
