# Lots NER à corriger (palier Silver)

Quatre lots de 60 phrases, **pré-remplis automatiquement par règles**
(`src/ner_juridique/regles.py`). Les pré-annotations contiennent des erreurs
et des oublis : elles ne deviennent un gold qu'après ta relecture.

| Fichier | Rôle | Après correction |
|---|---|---|
| `ner_dev_fr_v1.csv` | dev FR (les 60 phrases historiques N001–N060) | rester dans `data/dev/` |
| `ner_dev_ar_v1.csv` | dev AR | rester dans `data/dev/` |
| `ner_test_fr_v1.csv` | test FR | geler dans `data/test_locked/` + empreinte SHA-256 |
| `ner_test_ar_v1.csv` | test AR | geler dans `data/test_locked/` + empreinte SHA-256 |

Un article n'apparaît que dans un seul lot ; l'entraînement d'une langue exclut
les articles évalués dans cette langue (`data/silver/ner_silver_resume.json`).

## Comment corriger une ligne

1. Lire `entites_lisibles` : `[l'employeur]ROLE doit ...`.
2. Corriger la colonne **`entites`** (c'est la seule qui compte) au format
   `debut|fin|TYPE;debut|fin|TYPE` (positions de caractères dans `phrase`, base 0, fin exclue).
   Astuce : `python -X utf8 -m src.ner_juridique.positions "phrase" "texte de l'entité"`
   affiche les positions.
3. Passer **`statut`** de `a_verifier` à `verifie` (même si rien n'a changé).
4. Un doute → `commentaire`.

Ne pas modifier `phrase`. La colonne `entites_lisibles` est indicative ; elle
sera régénérée.

## Schéma (guide v1, complété pour l'arabe et les cas fréquents)

- **ROLE** : personne ou groupe porteur ou bénéficiaire d'une règle
  (« l'employeur », « tout salarié », « المؤجر », « رئيس المؤسسة », « الأطفال »).
- **INSTITUTION** : organisme, juridiction ou autorité nommée
  (« l'inspection du travail », « le Secrétaire d'Etat aux Affaires Sociales »,
  « تفقدية الشغل », « الصندوق الوطني للضمان الاجتماعي »).
  Une personne qui exerce une fonction (« l'inspecteur du travail », « متفقد الشغل ») est un ROLE.
- **DELAI** : durée ou échéance (« dans un délai de quinze jours », « أجل شهر »).
- **MONTANT** : somme ou quantité chiffrée (« 300 dinars », « 48 heures », « dix pour cent »).
  Un **âge** est un MONTANT (« âgés de moins de 18 ans », « دون 18 عاما ») — décision v2.

Règles propres à l'arabe :
- Les proclitiques **و ف ب ل ك** restent hors de l'entité : « وللمؤجر » → `لمؤجر`
  (l'article assimilé ل est gardé) ; « بتفقدية الشغل » → `تفقدية الشغل`.
- Le complément qui fait partie du nom de l'institution est inclus
  (« الوزير المكلف بالشؤون الاجتماعية »).

Ne pas annoter les renvois d'articles ni les références de lois.
