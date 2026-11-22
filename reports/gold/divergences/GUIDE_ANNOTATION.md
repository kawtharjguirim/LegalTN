# Guide — vérification des divergences AR / FR (Gold)

Fichier à remplir : `echantillon_annotation_60.csv` (60 articles tirés au hasard, graine 2026).
Ne pas ouvrir `echantillon_cle_predictions.csv` avant d'avoir fini (annotation à l'aveugle).

Pour chaque article, lire la version française et la version arabe dans le PDF du Code du travail (pages indiquées), puis :

- **verdict_humain** : `divergence` si les deux versions ne disent pas la même chose sur le fond ; `identique` sinon. Une différence de style ou de traduction libre n'est pas une divergence.
- **type_divergence** (si divergence) : `nombre` (délai, montant, pourcentage), `modal` (doit / peut / interdit), `negation`, `reference` (renvoi vers un autre article), `contenu_manquant` (phrase présente dans une seule langue), `autre`.
- **commentaire** : une phrase pour expliquer.

Double annotation : 2 personnes annotent les mêmes 60 lignes séparément (copier le fichier), pour calculer le kappa.
