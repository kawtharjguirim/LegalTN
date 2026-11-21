# Corrections du texte arabe numérisé (21 novembre 2026)

Commande : `python -X utf8 -m src.corpus.corriger_arabe` — lit `data/processed/corrections_ar.csv`, écrit
`data/processed/articles_ar_corrige.csv`. **Le fichier d'origine `articles_ar.csv` n'est pas modifié.** Le moteur
de recherche (`baseline_bm25.AR`) et l'extracteur de références utilisent le fichier corrigé s'il existe.
Chaque correction doit trouver sa chaîne « avant » **exactement une fois** (sinon la commande échoue). Tests :
`tests/test_corpus_arabe.py`.

## Ce qui a été corrigé : 20 corrections sur 14 articles

Colonne « vérification » : **image** = lu sur l'image de la page du PDF (13 corrections) ; **français** = déduit du
texte français de l'article équivalent, **à confirmer sur image** (7 corrections : les numéros d'articles cités
diffèrent entre les deux versions et seule l'arabe est incohérente).

| Article | Page | Correction | Vérification |
|---|---|---|---|
| AR-64 | p. 33 | `مدة 0 يوما` → `مدة 30 يوما` | image |
| AR-64 | p. 33 | `بما قدره 5 يوما` → `بما قدره 15 يوما` | image |
| AR-90 | p. 42 | `في الأسبوع : 29675 .` → `في الأسبوع : 75 % .` | image |
| AR-90 | p. 42 | `25 م إلى حدود السساعة 48 و9050 بعد ذلك` → `25 % إلى حدود الساعة 48 و50 % بعد ذلك` | image |
| AR-90 | p. 42 | `لوقت جزئى : 9050.` → `لوقت جزئي : 50 %.` | image |
| AR-287 | p. 95 | `و2779 و280 و2854 و286` → `و279 و280 و284 و286` | image |
| AR-425 | p. 130 | `بين 72 و2858 دينارا` → `بين 72 و288 دينارا` | image |
| AR-425 | p. 130 | `بخطية من 8 إلى 2880 دينارا` → `بخطية من 288 إلى 2880 دينارا` | image |
| AR-351 | p. 108 | `مطلب الفسخ في 2) إذا وقع` → `مطلب الفسخ في ظرف 3 أشهر. 2) إذا وقع` | image |
| AR-351 | p. 108 | `© في صورة تعود` → `5) في صورة تعود` | image |
| AR-234 | p. 84 | `بين 24 و 60 و53 إلى 56` → `بين 24 و 60 دينارا كل من خالف مقتضيات الفصول 5` | image |
| AR-234 | p. 84 | `127 إلى 9 و132` → `127 إلى 129 و132` | image |
| AR-94-14 | p. 45 | `و13-94 من هذه المجلة` → `و13-94 من هذه المجلة بالعقوبات المنصوص عليها ب` | image |
| AR-100 | p. 48 | `وفقا لأحكام الفصل 5 من هذه المجلة` → `وفقا لأحكام الفصل 95 من هذه المجلة` | francais |
| AR-87 | p. 41 | `المعينة بالفصل 5 ويبقى` → `المعينة بالفصل 85 ويبقى` | francais |
| AR-125 | p. 55 | `بالفصول من 7 إلى 111` → `بالفصول من 107 إلى 111` | francais |
| AR-176 | p. 73 | `عملا بالفصل 1 من هذه المجلة` → `عملا بالفصل 171 من هذه المجلة` | francais |
| AR-227 | p. 82 | `عملا بأحكام الفصل 6 والأحكام` → `عملا بأحكام الفصل 216 والأحكام` | francais |
| AR-265 | p. 91 | `في الفصل 0 ظروف` → `في الفصل 270 ظروف` | francais |
| AR-196 | p. 76 | `بالفصول 583 إلى 115` → `بالفصول 83 إلى 115` | francais |

Corrections qui changent **une règle** (toutes lues sur image) : **congé de maternité** (art. 64 : 30 et 15 jours,
et non « 0 » et « 5 »), **taux des heures supplémentaires** (art. 90 : 75 %, 25 %, 50 %), **amende** (art. 425 :
72 à 288 dinars, récidive 288 à 2880), **délai de 3 mois** de résiliation du contrat d'apprentissage (art. 351),
**liste des articles sanctionnés** (art. 234 : 5 bis, 8, 9, 21, 27 à 29, 31 absents ; « 127 à 9 » pour 127 à 129),
renvoi aux **sanctions des articles 234 à 237** (art. 94-14), renvois 279 et 284 (art. 287).

## Effet mesuré

- Renvois croisés arabes sans article correspondant : **3 → 0** (`« 0 »`, `« 2779 »`, `« 2854 »` disparus).
- Cohérence arabe/français des renvois : entrées identiques **68 → 75 sur 102 (66,7 % → 73,5 %)**.
- Écart de nombres des articles 64, 90, 425, 351, 287 : réduit (restent des dates et numéros de lois, légitimes).

## Ce qui reste

- **Non corrigé** : AR-344 (début bruité, délai de quinzaine et trois originaux absents), AR-335 (contenu français de
  l'article manquant), AR-24 (énumération plus courte), AR-351 : alinéas 7 et 8 (« 58) » à lire « 8) », sur la page
  suivante), et l'OCR « 3 » parasite d'autres articles ; 10 écarts de renvois arabe/français restent à examiner.
- **7 corrections « français »** à confirmer sur image (articles 87, 100, 125, 176, 196, 227, 265).
- Les résultats de recherche arabes des rapports Silver et Gold ont été mesurés **avant** ces corrections ; ils ne
  sont pas recalculés ici.
