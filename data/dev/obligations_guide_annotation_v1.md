# Guide d'annotation des obligations — v1 (lot B)

Auteure : Kawthar Jguirim. Date : 27 octobre 2026.
Statut : modèle vide. Aucune ligne n'est annotée. Valeurs de `modal` et découpage 200 dev / 100 test : validés par l'auteure le 27 octobre 2026. Les exemples ci-dessous sont des schémas, pas des annotations du corpus.

## 1. Objet

Une obligation est une phrase du Code du travail où un rôle doit faire une action, ne doit pas la faire, ou y est autorisé sous condition. Ce guide décrit comment la saisir dans `obligations_modele_v1.csv`.

## 2. Ce qu'on annote

- Une ligne par obligation. Si une phrase contient deux obligations distinctes, on fait deux lignes.
- La phrase est copiée telle quelle depuis le texte français de l'article (colonne `phrase`).
- On n'annote que ce qui est écrit dans l'article. On ne complète pas avec une connaissance extérieure.

## 3. Ce qu'on n'annote pas

- Les définitions (« on entend par… », « est dit… »).
- Les phrases descriptives qui emploient « doit » sans créer d'obligation pour un rôle (« la somme doit être… »). Elles vont dans `commentaire` avec la mention `non_obligation`.
- Les renvois à une autre obligation sans contenu propre (« dans les conditions prévues à l'article X »), sauf si la phrase crée une obligation à part entière.

## 4. Les champs

- **obligation_id** : identifiant (`O001`, `O002`, …). Rempli au moment de l'annotation.
- **article_fr** : article d'origine, sous la forme `FR-n` ou `FR-n-suffixe`.
- **page_fr** : page PDF où se trouve l'article (numérotation PDF).
- **phrase** : extrait exact du texte français. Pas de reformulation.
- **qui** : le rôle qui porte l'obligation, copié tel qu'écrit dans la phrase (par exemple « l'employeur », « le travailleur »). Si le texte ne nomme pas le rôle, laisser vide et le signaler dans `commentaire`.
- **modal** : un des trois termes suivants :
  - `obligation` : le rôle doit faire l'action ;
  - `interdiction` : le rôle ne doit pas faire l'action ;
  - `permission` : le rôle peut faire l'action, sous condition.
- **quoi** : l'action, copiée ou résumée au plus court en restant fidèle au texte.
- **quand** : la condition, le délai ou le moment, copié tel qu'écrit. Vide si le texte ne précise rien.
- **commentaire** : toute remarque de l'auteure (ambiguïté, `non_obligation`, rôle absent, phrase coupée par l'OCR, etc.).

## 5. Règles de saisie

- Recopier les termes du texte. Ne pas normaliser le rôle (« l'employeur » reste « l'employeur »). La normalisation sera une décision séparée.
- En cas de doute entre `obligation` et `permission`, mettre le doute dans `commentaire` et choisir le terme le plus proche de la phrase.
- Une phrase mal coupée par l'OCR est signalée dans `commentaire`, avec la page à vérifier sur image.

## 6. Découpage prévu

- Dev : 200 obligations, pour concevoir les règles.
- Test gelé : 100 obligations, à ne pas utiliser avant la mesure, et une seule fois.
- Le total de 300 correspond au gold demandé par le cahier. Les 300 sont annotées par l'auteure ; aucune n'est remplie par l'assistant.

## 7. Limite connue

Un seul annotateur : le kappa ne peut pas être calculé. Ce point doit être dit en revue.
