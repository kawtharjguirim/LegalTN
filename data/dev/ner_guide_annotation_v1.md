# Guide d'annotation NER — v1 (lot N)

Statut : modèle vide. Aucune ligne n'est annotée. Ce guide décrit le schéma
d'entités nommées utilisé par le composant NER par CRF de LegalTN.

## 1. Objet

On annote dans les phrases du Code du travail les mentions utiles à la
compréhension des articles : rôles porteurs d'obligations, institutions,
délais et montants. Une ligne de `ner_a_annoter_v1.csv` contient une phrase ;
les entités se saisissent dans `entites` au format :

```
debut|fin|TYPE;debut|fin|TYPE;...
```

`debut` et `fin` sont les positions de caractères dans `phrase` (base 0,
`fin` exclue), séparées par `|`. Les entités ne se chevauchent pas.

## 2. Types d'entités

- **ROLE** : personne ou groupe porteur ou bénéficiaire d'une règle
  (« l'employeur », « le travailleur », « les conseillers prud'hommes »,
  « tout salarié »).
- **INSTITUTION** : organisme, juridiction ou autorité nommée
  (« la caisse nationale de sécurité sociale », « l'inspection du
  travail », « le Conseil de la Formation Professionnelle »).
- **DELAI** : durée ou échéance explicite (« dans les quinze jours »,
  « au moins un mois avant »).
- **MONTANT** : somme ou quantité chiffrée (« 50 dinars », « 40 heures »,
  « dix pour cent »).

## 3. Règles

- Copier l'étendue minimale qui désigne l'entité ; inclure le déterminant
  si la lecture naturelle l'exige (« l'employeur » plutôt que « employeur »).
- Ne pas annoter les renvois d'articles (« article 254 ») ni les titres de
  chapitre : ils relèvent de l'alignement, pas du NER.
- Un mot ambigu prend le type du rôle qu'il joue dans la phrase.
- En cas de doute : meilleure annotation + remarque dans `commentaire`.

## 4. Limite connue

Un seul annotateur : le kappa inter-annotateurs ne peut pas être calculé.
Le dire en revue.
