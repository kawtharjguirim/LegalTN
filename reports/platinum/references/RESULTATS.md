# Références croisées — extraction et contrôle (21 novembre 2026)

Commande : `python -X utf8 -m src.obligation_extraction.references_croisees`
Code : `src/obligation_extraction/references_croisees.py` ; tests : `tests/test_references_croisees.py`.
Sorties : `references_fr.csv`, `references_ar.csv` (une ligne par mention), `graphe_fr.csv`,
`graphe_ar.csv` (arêtes article → article cité), `coherence_ar_fr.csv`, `resume.json`.

## Méthode

Règles à base de motifs, sans apprentissage, en français et en arabe. Pour chaque mention :
- **type** : `interne` (un autre article du Code), `externe` (autre texte : Code pénal, Code des
  obligations et des contrats, loi ou décret nommé), `relative` (« l'article précédent », « الفصل السابق »,
  « les trois articles précédents ») résolue d'après l'article source ;
- **cibles** : numéros d'articles ; listes (« 234, 236 et 237 ») et plages (« 53 à 56 », « 7 إلى 111 »)
  développées ; suffixes (`bis`, `ter`, `مكرر`) et sous-articles (`94-4`) conservés ;
- **portée** : « du présent code / chapitre / titre », nom du texte externe, ou `implicite`.

Particularités traitées : intitulés d'articles et de plages abrogées (« Article 21-2 (Ajouté par la
loi…).- », « Articles 272 à 277 (Abrogés… ») **exclus** (ce ne sont pas des renvois) ; numéros composés
arabes écrits à l'envers par l'OCR (« 4-94 » pour 94-4) remis dans l'ordre.

## Résultats sur le Code

| | Français (498 articles) | Arabe (477, hors abrogés) |
|---|---:|---:|
| Mentions extraites | 176 | 147 |
| dont internes / externes / relatives | 125 / 34 / 17 | 114 / 23 / 10 |
| Articles contenant un renvoi | 132 | 116 |
| Cibles internes | 313 | 265 |
| **Cibles sans article correspondant** | **0** | **0** (3 avant correction du texte arabe) |
| Cibles vers un article abrogé | 14 | 10 |

Avant la correction du texte arabe, 3 cibles arabes n'avaient pas d'article : « الفصل 0 » (art. 265) et « 2779 »,
« 2854 » pour 279 et 284 (art. 287) — des **défauts d'OCR** repérés par ce contrôle puis corrigés (voir
`reports/platinum/corpus_arabe/RESULTATS.md`). Les chiffres ci-dessus sont ceux du texte arabe **corrigé** ; le nombre
de cibles arabes baisse (303 → 265) surtout parce que « الفصول من 7 إلى 111 » (105 articles) était en fait « 107 à 111 ».

## Contrôle de cohérence arabe / français

Les deux versions d'un article doivent citer les mêmes articles. Comparaison par entrée française
(union des renvois des articles arabes alignés), sur **102** entrées qui contiennent un renvoi :

| | Avant correction du texte arabe | Après |
|---|---:|---:|
| Entrées aux renvois **identiques** | 68 (66,7 %) | **75 (73,5 %)** |
| Entrées aux renvois différents | 17 | 10 |
| Renvoi d'un seul côté | 17 | 17 |

Les écarts initiaux étaient en grande partie des **défauts d'OCR du texte arabe** (art. 87, 100, 125, 176, 227, 265,
287, plus les articles 94-14 et 234 aux listes tronquées) : le contrôle a servi à les trouver, puis ils ont été
corrigés. Les 7 corrections déduites du français (articles 87, 100, 125, 176, 196, 227, 265) sont **à confirmer sur
image**. Les écarts restants viennent surtout de listes d'infractions répétées en français (articles 21, 234, 334, 386,
428 renvoient aux sanctions 234 à 237) ou d'extractions françaises incomplètes, pas toujours d'un défaut arabe.

## Précision (estimation sur échantillon, jugée par Claude)

Un échantillon aléatoire de 35 mentions (20 FR, 15 AR) a été relu avant les derniers correctifs
(`seed 7`, après un premier échantillon de 45 mentions qui a servi à corriger les règles) :
**32 correctes sur 35 (91 %)** — FR 19/20, AR 13/15. Erreurs observées : un intitulé mal formé par l'OCR
pris pour un renvoi (corrigé depuis), une liste arabe aux séparateurs dégradés (seul le premier article
retenu), un renvoi à « مجلة الشغل » classé externe (corrigé depuis). **Aucun gold humain n'existe** : ce
chiffre est une estimation à confirmer. Le rappel n'a pas été mesuré (des renvois formulés autrement,
par exemple « les dispositions ci-dessus », ne sont pas extraits).

## Limites

- Règles, pas d'analyse de dépendances ; « et suivants » est signalé mais non développé.
- Plage `7 إلى 111` développée en 105 articles : elle est exacte ici, mais une plage mal numérisée
  produirait des arêtes fausses (limite : 150 articles).
- Les renvois sans nom de texte (portée `implicite`, 75 en français) sont supposés internes.
- Les renvois à des alinéas ou paragraphes (« paragraphe a ») sont ignorés.
