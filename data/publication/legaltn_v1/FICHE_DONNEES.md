# Fiche de données — LegalTN v1 (21 novembre 2026)

Jeu de données bilingue (arabe / français) autour du **Code du travail tunisien**. Version `v1`,
préparée pour publication ; **non publiée tant que la licence n'est pas clarifiée** (voir `LICENCE.md`).

## 1. Ce que contient le dossier

| Fichier | Lignes | Contenu |
|---|---:|---|
| `alignement_fr_ar_v1.csv` | 519 | Paires d'articles arabe ↔ français : numéros, pages du PDF, statut (apparié, abrogé, hors Code), similarité LaBSE, écart de nombres. **Sans le texte des articles.** |
| `obligations_dev_v1.csv` | 200 | Annotation de phrases du texte français : `qui`, `modal` (obligation / interdiction / permission), `quoi`, `quand`, commentaire. **Sans la phrase source** : elle est remplacée par son empreinte `phrase_sha256` (16 premiers caractères du SHA-256 de la phrase aux espaces normalisés). |
| `questions_dev_v1.csv` | 107 | Questions de développement FR (44), arabe (24), tunisien (39) avec l'article de référence (vide pour les questions hors périmètre). |
| `CHECKSUMS.sha256` | | Empreintes des fichiers. |

Absents volontairement : le **texte des articles** (licence), le **jeu de test des obligations**
(100 phrases, à publier seulement après la mesure finale, qui ne se fait qu'une fois), les
questions de test gelées (`data/test_locked/`).

## 2. Source

Code du travail tunisien, édition bilingue AR/FR (PDF de 291 pages), numérisée par OCR puis
segmentée en articles : 515 entrées arabes, 498 entrées françaises. Les numéros d'articles et les
pages renvoient à ce PDF. **Aucune donnée personnelle** : textes de loi et questions rédigées pour
le projet.

## 3. Fabrication et statut des annotations

| Élément | Qui | Statut | Limite |
|---|---|---|---|
| Alignement (494 paires) | règles de numérotation (Bronze), contrôlé par LaBSE et e5 | 160 paires vérifiées sur image par l'auteure ; accord 0,98 avec les embeddings | le contrôle porte surtout sur des paires que la numérotation a produites : biais favorable |
| Obligations (200 dev) | **pré-annotation par Claude**, `statut = verifie_claude` | **à relire** ; `verifie` = relu par un humain | un seul annotateur ; kappa inter-annotateurs non calculable |
| Questions FR (44 + 3 AR + 9 tun) | auteure | `verifie` | dev déjà consulté pour régler les seuils |
| Questions AR traduites (21), tunisiennes (30) | Claude | `a_valider` | formulations à relire (derja en particulier) |

Répartition des 200 obligations dev : 114 obligations, 53 interdictions, 4 permissions,
29 phrases non retenues (`commentaire` commençant par `non_obligation`). **Les phrases candidates
ont été choisies pour contenir un marqueur modal** : le dev contient très peu de permissions
(« peut »), que le test contient à 50 %. Une mesure sur le dev ne dit donc rien de la détection des
permissions.

## 4. Défauts connus du texte arabe (OCR)

L'audit des divergences AR/FR n'a trouvé **aucune divergence juridique réelle**, mais 8 articles dont
le texte arabe contient une erreur qui change une règle : art. 64 (congé de maternité : 0 et 5 jours
pour 30 et 15), art. 90 (taux d'heures supplémentaires), art. 425 (2858 pour 288 dinars), art. 351
(délai de 3 mois absent), art. 234 et 94-14 (listes de sanctions incomplètes), renvois 2779 / 2854
(279 / 284). L'alignement (numéros, pages) n'est pas affecté ; le texte arabe l'est. Détail :
`reports/gold/divergences/RESULTATS.md`.

## 5. Usages et limites

- Usage prévu : recherche et évaluation de systèmes de question-réponse juridiques bilingues,
  extraction d'obligations, étude de l'alignement AR/FR.
- **Pas un avis juridique.** Le Code a été modifié depuis cette édition ; ne pas utiliser pour
  conseiller une personne.
- Les questions dev ont servi à régler les seuils d'abstention : ne pas les réutiliser comme test.
- Pour ajouter les phrases sources (variante `--avec-phrases`), clarifier d'abord la licence.

## 6. Reproduire

```
python -X utf8 -m src.publication.preparer           # régénère ce dossier
python -X utf8 -m src.publication.preparer --avec-phrases --avec-test   # variante complète (après licence et mesure finale)
```
