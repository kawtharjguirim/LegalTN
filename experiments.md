# Journal des expériences — LegalTN

Chaque entrée indique la date, l'objectif, la configuration, les graines, les résultats et la décision prise.
Ne jamais modifier une entrée passée : ajouter une nouvelle entrée pour corriger.

## Modèle d'entrée

```
## AAAA-MM-JJ — Titre court
- Objectif :
- Composant / lot :
- Jeu utilisé : (dev / test_locked — le test_locked ne sert jamais au réglage)
- Configuration :
- Graines : 
- Résultats (moyenne ± écart-type) :
- Baseline classique :
- Baseline neuronale :
- Erreurs analysées (≥ 30 pour un composant appris) :
- Décision et suite :
```

## Jeu de test fixé

- Date de fixation : 2026-10-27 (tirage des paires d'alignement, graine 20261027)
- Version / hash du fichier `data/test_locked/` : alignement_candidats_v1.csv, sha256 9e37dc4c80f2f84ac3019f891f7ca98ee6aa13e47724b5ea47d955fed278ba0b
- Nombre de questions : aucune question à ce stade (cible 200 : FR / AR / tunisien) — hors périmètre : (cible 40)
- Nombre de paires d'alignement : 30 (lot A, tirées parmi 397 paires non consultées) ; annotations faites le 2026-10-27 dans alignement_gold_v1.csv (validées par Kawthar)
- Qui a rédigé les questions de référence : n/a

---

## 2026-10-21 — Cadrage initial
- Objectif : créer la structure du dépôt et le cahier des charges (phase 1).
- Composant / lot : cadrage (toutes lots).
- Jeu utilisé : aucun.
- Configuration : Python 3.11+, arborescence du guide.
- Graines : n/a.
- Résultats : n/a.
- Décision et suite : valider le périmètre (Code du travail), puis inventorier les sources officielles.

---

## 2026-10-27 — Gel du test d'alignement (test_locked v1)
- Objectif : figer un jeu de test d'alignement distinct des paires utilisées pour régler les règles.
- Composant / lot : alignement par numérotation (lot A), 03 v5.
- Jeu utilisé : test_locked (écriture seule ; aucune mesure faite).
- Configuration : tirage aléatoire sans remise, graine 20261027, script `src/evaluation/tirage_test_v1.py`. Exclusion des 57 numéros d'articles consultés (vérification, corrections FR, notes vérifiées, contrôles d'années, articles abrogés ou corrigés à la main). 397 paires éligibles, 30 tirées.
- Graines : 20261027.
- Résultats : n/a (pas encore annotés).
- Baseline classique : à définir (appariement par position, copie de la source).
- Baseline neuronale : n/a.
- Erreurs analysées : n/a.
- Décision et suite : annoter les 30 paires dans `data/test_locked/alignement_gold_v1.csv` (article FR attendu, vérification sur image des deux pages), puis calculer précision et rappel. Ne pas modifier `alignement_candidats_v1.csv` : son hash est consigné ci-dessus.

---

## 2026-10-27 — Annotation du test d'alignement et mesure (test_locked v1)
- Objectif : annoter les 30 paires gelées et mesurer la précision de l'alignement par numérotation.
- Composant / lot : alignement par numérotation (lot A), 03 v5.
- Jeu utilisé : test_locked v1 (alignement_candidats_v1.csv, sha256 9e37dc4c80f2f84ac3019f891f7ca98ee6aa13e47724b5ea47d955fed278ba0b, inchangé).
- Configuration : annotation de chaque paire sur l'image de la page (tête d'article et page), sans modification des règles.
- Graines : 20261027 (tirage).
- Résultats : précision = 28/30 = 93,3 % (paires correctes parmi les paires proposées par l'algorithme). Rappel non mesuré : le test ne contient que des paires candidates.
- Baseline classique : à mesurer (appariement par position).
- Baseline neuronale : n/a.
- Erreurs analysées (2) :
  - T007 AR-76-2 (p. 38) apparié à FR-76 : le texte 76-2 (p. 253) est absorbé dans la ligne FR-76 (segmentation française).
  - T022 AR-233 مكرر (p. 84) apparié à FR-233 : l'équivalent est « Article 233 bis » (p. 202), ligne distincte ; le suffixe est perdu à l'appariement.
- Limites : annotation faite par une seule personne (kappa non calculable) ; vérification limitée à la tête d'article et à la page, pas au texte entier.
- Décision et suite : corriger les deux cas dans un nouveau notebook (pas dans le test) ; fichier gold = alignement_gold_v1.csv, sha256 24c0aedb473a026f0859872ee774cacc2e910da92e62325ea3f7a51b23e3d574.

---

## 2026-10-27 — Baseline « même numéro » sur le test d'alignement v1
- Objectif : comparer l'alignement par règles à une baseline triviale sur le test gelé.
- Composant / lot : alignement par numérotation (lot A), 03 v5.
- Jeu utilisé : test_locked v1 (alignement_gold_v1.csv, 30 paires). Lecture seule.
- Configuration : baseline = pour chaque article arabe, première entrée française de même numéro (sans suffixe) dans articles_fr_corrige.csv ; correct si l'intitulé (suffixe compris) et la page concordent avec le gold. Script : src/evaluation/baseline_meme_numero.py.
- Graines : n/a.
- Résultats : baseline même numéro = 26/30 = 86,7 % ; alignement par règles = 28/30 = 93,3 %. Écart : 2 paires.
- Baseline classique : même numéro (ci-dessus).
- Baseline neuronale : n/a.
- Erreurs de la baseline (4) : T001 et T002 (14 bis, 14 ter : même numéro 14 mais suffixe ignoré), T007 (76-2), T022 (233 bis). Les quatre cas portent sur des articles à suffixe.
- Décision et suite : le gain de l'alignement par règles sur la baseline est faible (2 paires sur 30, petit échantillon) et ne tient qu'aux cas à suffixe. À présenter comme tel. La baseline par position (plan initial) reste à mesurer. Corriger les cas T007 et T022 dans un notebook séparé, puis mesurer sur le même test.

---

## 2026-10-27 — Correction de l'annotation T007 et T022 (test_locked v1)
- Objectif : corriger deux annotations de l'entrée du même jour, dont l'analyse était fausse.
- Composant / lot : alignement par numérotation (lot A), 03 v5.
- Jeu utilisé : test_locked v1 (alignement_candidats_v1.csv, inchangé ; lecture de la ligne fr_ligne 107 et 293 de articles_fr_corrige.csv).
- Constat : l'algorithme a bien apparié T007 (AR-76-2) à la ligne française 107 « Article 76-2 » (p. 253) et T022 (AR-233 مكرر) à la ligne 293 « Article 233 bis » (p. 202). Les deux paires sont correctes. L'erreur est dans l'annotation, qui lisait l'étiquette article_fr « FR-76 » / « FR-233 » sans vérifier la ligne.
- Résultats corrigés : alignement par règles = 30/30 = 100 % sur les paires candidates (au lieu de 28/30). Baseline même numéro inchangée : 26/30 = 86,7 %.
- Problème réel à noter (sans effet sur l'appariement) : la ligne FR-76 « Article 76-2 » contient en fin de texte l'en-tête « Chapitre V Travaux spéciaux ... » ; à traiter comme les autres en-têtes absorbés (liste ouverte).
- Décision et suite : corriger T007 et T022 dans alignement_gold_v1.csv (bon_appariement = oui) après validation de Kawthar ; le fichier candidats reste inchangé. Les entrées précédentes ne sont pas modifiées ; la mesure à retenir est 30/30 après cette correction.

---

## 2026-10-27 — Analyse des erreurs OCR corrigées (Tableau 3, composant segmentation / OCR)
- Objectif : catégoriser les erreurs corrigées du texte (exigence du guide : au moins 30 erreurs, 4 à 6 catégories).
- Composant / lot : OCR et segmentation (lot A), notebooks 02 v15 et 04 v2.
- Jeu utilisé : journaux de corrections existants (articles_ar.csv, corrections_fr.csv). Aucune donnée modifiée.
- Configuration : script `src/evaluation/analyse_erreurs_ocr.py`, sortie `data/processed/erreurs_ocr_categorisees.csv`, tableau `data/processed/tableau3_erreurs_ocr.csv`.
- Résultats : 275 erreurs corrigées, 5 catégories : année de la loi citée (164), confusion ى / ي (56), autre erreur de mot ou de caractère (46), caractère parasite (7), texte d'une autre partie absorbé (2).
- Limite : pour les 158 dates d'amendement, les valeurs avant/après ne sont pas journalisées ; les exemples sont donc vides pour cette catégorie.
- Décision et suite : journaliser avant/après pour les dates dans un prochain notebook, sans rejouer les corrections.

---

## 2026-10-27 — Gold corrigé et baseline par position (test_locked v1)
- Objectif : appliquer la correction d'annotation validée (T007, T022) et mesurer la baseline par position relative.
- Composant / lot : alignement par numérotation (lot A), 03 v5.
- Jeu utilisé : test_locked v1. Fichier candidats inchangé (sha256 9e37dc4c80f2f84ac3019f891f7ca98ee6aa13e47724b5ea47d955fed278ba0b). Fichier gold modifié : alignement_gold_v1.csv, sha256 a372fd73523ccefabbe9e6d0eca0b956c914598711ba40b0fbe44a09de54aeee.
- Configuration : baseline position = pour chaque article arabe non abrogé de rang k parmi 477, l'entrée française de rang round(k × (494−1)/(477−1)) dans l'ordre du document (pages PDF décroissantes, hors pp. 288–289). Script `src/evaluation/baseline_position.py`. Correct si intitulé (suffixe compris) et page concordent avec le gold.
- Graines : n/a.
- Résultats :
  - alignement par règles : 30/30 = 100 % (corrigé ; 28/30 avant correction d'annotation) ;
  - baseline « même numéro » : 26/30 = 86,7 % ;
  - baseline « position relative » : 5/30 = 16,7 %.
- Baseline neuronale : n/a.
- Erreurs analysées : aucune erreur d'alignement sur le test après correction.
- Limites : une seule annotatrice (kappa non calculable) ; mesure de précision seulement (le test ne contient que des paires candidates, donc pas de rappel) ; 30 paires seulement.
- Décision et suite : présenter 100 % avec ces limites. Construire le test de rappel à partir de paires non candidates si nécessaire.

---

## 2026-10-27 — Gel du jeu de 40 questions de référence (test_locked v1)
- Objectif : figer le premier jeu de questions de référence, pour mesurer la réponse du système plus tard.
- Composant / lot : RAG et abstention (phase 2 du cahier des charges, non encore construite).
- Jeu utilisé : questions_reference_v1.csv (écriture seule ; aucune mesure faite).
- Configuration : 40 questions : 31 dans le périmètre (27 FR, 9 AR, 4 tunisien ; une question peut compter dans deux langues), 3 présupposés faux, 6 hors périmètre. Chaque question dans le périmètre renvoie à un article ; la réponse attendue est rédigée à partir du texte français.
- Graines : n/a.
- Résultats : n/a.
- Baseline classique : à définir (BM25 sur les articles FR).
- Baseline neuronale : n/a.
- Erreurs analysées : n/a.
- Limites : les réponses en arabe n'ont pas encore été vérifiées sur image (article 19 : texte OCR brouillé) ; le gel ne peut être modifié sans nouvelle version (questions_reference_v2.csv). Les questions tunisiennes doivent être relues par un locuteur tunisien.
- Décision et suite : construire BM25 et mesurer le rappel@5 et la précision des citations sur ce jeu.

---

## 2026-10-27 — Vérification sur image des réponses arabes (questions_reference_v1)
- Objectif : vérifier sur les images des pages les 9 réponses attendues en arabe, avant toute mesure.
- Composant / lot : RAG et abstention (jeu de référence).
- Jeu utilisé : questions_reference_v1.csv (lecture seule ; fichier gelé non modifié).
- Configuration : pages PDF 14, 16, 31, 41, 51, 72, 81, 91, 131 lues en pleine résolution.
- Résultats : 8 réponses sur 9 confirmées (articles 14 bis, 19, 58, 88, 115, 175, 221, 265). Pour 88, la réponse dit « ألفان » alors que le texte porte « ألفين » (même chiffre, forme grammaticale différente).
- Erreur relevée : article 427 (page 131) : le texte dit « كاتب الدولة للتخطيط والاقتصاد الوطني », après « استشارة لجنة منح البطاقة المهنية ». La réponse v1 disait « وزير الدولة » et « اللجنة المختصة ». La question v1 disait aussi « لعون الخبز ».
- Décision et suite : ne pas modifier v1. Proposer questions_reference_v2.csv avec la réponse et la question 427 corrigées (fichier en attente de validation, hors test_locked). Les réponses françaises ne sont pas encore vérifiées sur image.

---

## 2026-10-27 — Correction de l'entrée de vérification arabe (questions_reference_v1)
- Constat : l'entrée précédente annonçait une erreur sur l'article 427. Vérification faite, le jeu v1 ne contient aucune question sur l'article 427 : la question et sa réponse ont été perdues lors d'une régénération du brouillon. Le fichier gelé est intact (sha256 3fb11fe40e3192f7a961abe1bacbfccf31d1139b86bd954056b28a7554bda03c).
- Résultat réel : les 8 questions arabes dans le périmètre sont confirmées sur image (articles 14 bis, 19, 58, 88, 115, 175, 221, 265). La 9e question arabe est hors périmètre (visa) et n'a pas de réponse attendue à vérifier.
- Pour 88, la réponse dit « ألفان » alors que le texte porte « ألفين » (forme grammaticale seulement).
- Décision et suite : pas de questions_reference_v2 pour l'instant. Si vous voulez tester l'article 427 (texte exact : « كاتب الدولة للتخطيط والاقتصاد الوطني » après « استشارة لجنة منح البطاقة المهنية »), il faudra une version v2 avec une question ajoutée, à valider. Les réponses françaises restent à vérifier sur image.

---

## 2026-10-27 — Vérification sur image des réponses françaises et gel de questions_reference_v2 (test_locked v2)
- Objectif : vérifier sur les images les réponses françaises du jeu de référence, corriger ce qui est faux ou incomplet, puis figer la version corrigée.
- Composant / lot : RAG et abstention (jeu de référence).
- Jeu utilisé : questions_reference_v1.csv (lecture seule ; fichier gelé non modifié, sha256 3fb11fe40e3192f7a961abe1bacbfccf31d1139b86bd954056b28a7554bda03c). Nouvelle version gelée : questions_reference_v2.csv dans test_locked, sha256 calculé à la date du gel (voir ci-dessous).
- Configuration : pages PDF 150, 153, 187, 194, 203, 204, 207, 215, 233, 239, 240, 242, 249, 260, 276, 279 lues en pleine résolution. Vérifiées : Q01 à Q19 (françaises, dans le périmètre) et Q32, Q34 (présupposées fausses) ; Q33 vérifiée puis corrigée. Non vérifiées sur image : Q35 à Q40 (hors périmètre, pas de page attendue) et Q28 à Q31 (tunisien).
- Modifications v1 → v2 (seules lignes changées) :
  - Q03 (article 58) : la réponse ajoute l'exception de l'alinéa 3 (inspection du travail, après avis de l'inspection médicale : emploi dès 16 ans pour les travaux listés, sous conditions de santé, sécurité, moralité et formation). La v1 disait seulement « dix-huit ans », ce qui était incomplet.
  - Q33 (présupposée fausse, article 58) : même ajout dans la réponse « Faux ».
  - Q30 (tunisien, article 58) : même ajout ; à relire par un locuteur natif.
- Résultats :
  - 18 réponses françaises confirmées telles quelles (Q01, Q02, Q04 à Q19) ; pour Q12 (article 427), le texte imprimé contient les coquilles « Sectaire » et « Economie » ; la réponse reste correcte sur le fond ;
  - Q03 nuancée (voir ci-dessus) ;
  - présupposées : Q32 et Q34 confirmées, Q33 corrigée.
- Décision : la question arabe sur l'article 427 n'est pas ajoutée à la v2 (proposition optionnelle, non validée). Elle pourra faire l'objet d'une v3 si validée.
- Remplace la décision de l'entrée précédente « pas de questions_reference_v2 pour l'instant ».
- Baseline classique : n/a. Baseline neuronale : n/a. Erreurs analysées : n/a.
- Limites : la vérification sur image est faite par l'assistant, validée par Kawthar Jguirim ; relecture tunisienne (Q28 à Q31, dont Q30 modifiée) à faire avant toute mesure ; l'article 427 imprimé contient des coquilles reprises telles quelles dans le corpus ; questions hors périmètre non vérifiables sur page.
- Décision et suite : utiliser questions_reference_v2.csv comme jeu de référence pour toute mesure RAG future. Conserver v1 comme trace du gel initial. Relecture tunisienne avant la mesure.

---

## 2026-10-27 — Empreinte du gel de questions_reference_v2 (test_locked v2)
- Précision à l'entrée précédente : questions_reference_v2.csv est gelé dans data/test_locked/ le 2026-10-27, sha256 0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083.
- Fichier v1 inchangé (sha256 3fb11fe40e3192f7a961abe1bacbfccf31d1139b86bd954056b28a7554bda03c).
- Décision : ces deux empreintes servent de référence pour vérifier qu'aucune des deux versions n'a été modifiée.

---

## 2026-10-27 — Baseline BM25 sur questions_reference_v2 (test_locked v2)
- Objectif : première mesure de référence du RAG (récupération seule), avant tout composant neuronal.
- Composant / lot : RAG, récupération lexicale (baseline classique).
- Jeu utilisé : questions_reference_v2.csv (lecture seule, sha256 0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083). Jeu gelé, non modifié.
- Corpus : FR = articles_fr_corrige.csv (498 entrées) pour les questions françaises et tunisiennes ; AR = articles_ar.csv (515 entrées) pour les questions arabes. Intitulé d'article reconstruit depuis le texte (suffixe bis / ter / quater compris).
- Configuration : BM25 standard, k1 = 1,5, b = 0,75, idf de Lucene. Tokenisation : FR en minuscules sans accents, stop-words français ; AR sans diacritiques, alef et ى/ي, ة/ه unifiés, stop-words arabes. Pas de racinisation. Requête = texte de la question seulement.
- Paramètres non réglés sur le test : valeurs standards, aucune variante essayée.
- Script : src/evaluation/baseline_bm25.py ; sortie : data/processed/baseline_bm25_v2_resultats.csv.
- Graines : n/a (déterministe).
- Mesure : rappel@1 et rappel@5 de l'article de référence. Exclues : 6 questions hors périmètre (pas d'article de référence) ; l'abstention n'est donc pas mesurée ici.
- Résultats (n = 34) :
  - ensemble : R@1 = 21/34 = 61,8 % ; R@5 = 29/34 = 85,3 % ;
  - français (n = 22) : R@1 = 72,7 % ; R@5 = 95,5 % ;
  - arabe (n = 8, corpus AR) : R@1 = 62,5 % ; R@5 = 87,5 % ;
  - tunisien (n = 4, corpus FR) : R@1 = 0 % ; R@5 = 25 % ;
  - dans le périmètre (n = 31) : R@1 = 61,3 % ; R@5 = 83,9 % ;
  - présupposées fausses (n = 3) : R@1 = 66,7 % ; R@5 = 100 %.
- Erreurs analysées (ratés, 13 questions avec R@5 = 0 ou R@1 = 0) : Q08 (absent du top 5 : « récusés » du texte contre « récusé » dans la question, pas de racinisation) ; Q25 (arabe, absent du top 5) ; Q29, Q30, Q31 (tunisien, absents du top 5) ; Q34 (présupposée, rang 5 seulement). Les autres ratés sont des rangs 2 à 5 (Q04, Q06, Q07, Q13, Q20, Q27, Q28).
- Baseline neuronale : n/a.
- Limites : mesure de récupération seule, sans génération ni citation vérifiée ; questions tunisiennes en écriture latine mixte, sans correspondance lexicale avec le texte ; aucune question hors périmètre mesurée ; 34 questions seulement, donc un écart de quelques questions change beaucoup le pourcentage.
- Décision et suite : garder cette baseline comme point de comparaison. Toute amélioration (racinisation, normalisation des suffixes, index multilingue) doit être mesurée sur ce même jeu et notée comme nouvelle entrée, sans réglage itératif sur le test. Relecture tunisienne toujours à faire.

---

## 2026-10-27 — Démo de bout en bout (src/demo/repondre.py) mesurée sur questions_reference_v2 (test_locked v2)
- Objectif : première chaîne complète, question brute -> article cité ou abstention, sans LLM ni API payante (exigence du guide).
- Composant / lot : RAG (récupération BM25 + règle d'abstention) ; démo de bout en bout.
- Jeu utilisé : questions_reference_v2.csv (lecture seule, sha256 0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083). Jeu gelé, non modifié.
- Configuration : détection de langue (présence de caractères arabes) ; BM25 k1 = 1,5, b = 0,75 (mêmes paramètres que la baseline) ; corpus FR ou AR ; règle d'abstention fixée a priori : abstention si aucun terme de contenu de la question n'apparaît dans le corpus de la langue détectée. Aucun seuil de score, aucune règle réglée sur le test.
- Script : src/demo/repondre.py ; sortie : data/processed/demo_bout_en_bout_v2_resultats.csv.
- Graines : n/a.
- Résultats :
  - dans le périmètre (n = 34) : R@1 = 21/34 et R@5 = 29/34 (identique à la baseline BM25 : cohérence vérifiée) ; abstention à tort = 0/34 ;
  - hors périmètre (n = 6) : abstention = 0/6.
- Erreurs observées : la règle d'abstention ne fonctionne pas. Les questions hors périmètre partagent des mots généraux (« salaire », « Tunisie », « cassation », « conseil ») avec le corpus, donc aucune n'est refusée. Exemple : « salaire minimum garanti en Tunisie » renvoie l'article 134 (texte sur la rémunération), ce qui est une réponse fausse présentée comme pertinente. Q01 renvoie l'article 14 au lieu de 14 bis en premier rang.
- Baseline neuronale : n/a. Baseline classique : BM25 (voir entrée précédente).
- Limites : la démo renvoie un extrait de l'article, pas une réponse rédigée ; l'abstention n'est pas mesurable tant qu'une règle n'est pas choisie ; mesure faite sur le test gelé, donc à ne pas utiliser pour régler la règle.
- Décision et suite : ne pas régler la règle d'abstention sur le jeu de test. Il faut un jeu de développement séparé (questions hors périmètre et dans le périmètre, distinct de test_locked) pour choisir un seuil ou une règle, puis une seule mesure sur le test. Consigner cette décision avant toute nouvelle mesure.

---

## 2026-10-27 — Jeu de développement et choix de la règle d'abstention (data/dev, hors test_locked)
- Objectif : choisir une règle d'abstention sans régler quoi que ce soit sur le test gelé.
- Composant / lot : RAG et abstention (démo de bout en bout).
- Jeu utilisé : data/dev/questions_dev_v1.csv (28 questions : 13 dans le périmètre dont 1 tunisienne, 15 hors périmètre dont 1 arabe et 1 tunisienne ; sha256 1a685a4081ee48f5768e80f3c723ad381acad0e8f84866edd73f72f422b2467a). Rédigées à partir des textes du corpus (articles 23, 68, 118, 124, 140, 147, 183, 193, 252, 268, 366, 402) ; pas de chevauchement avec le test gelé. Les réponses FR ne sont pas vérifiées sur image.
- Configuration : règles comparées sur le dev uniquement : A (aucun terme présent), B (part des termes présents < c), C (meilleur score BM25 < s). Script : src/evaluation/choisir_regle_abstention.py ; tableau : data/dev/choix_regle_abstention.csv.
- Résultats dev :
  - règle A : 0 hors abstenu, 0 fausse abstention ;
  - règle B : 0 hors abstenu jusqu'à c = 0,30 ; à partir de c = 0,35, une fausse abstention apparaît ; 10/15 hors abstenus au mieux, avec 3 fausses abstentions ;
  - règle C : seuils 9,04 et 9,13 donnent 13/15 hors abstenus et 0 fausse abstention ; retenue : s = 9,085 (milieu de la plage).
- Décision : règle C figée dans src/demo/repondre.py (SEUIL_SCORE_MIN = 9,085), en plus de la règle « aucun terme présent ». Le choix est fait sur 28 questions seulement, donc fragile.
- Limites : jeu de développement très petit ; un seuil de score BM25 dépend de la longueur de la question.
- Suite : une seule mesure sur le test avec cette règle (entrée suivante).

---

## 2026-10-27 — Mesure unique sur test_locked v2 avec la règle d'abstention figée
- Objectif : mesure finale de la démo avec la règle choisie sur le dev.
- Composant / lot : RAG et abstention.
- Jeu utilisé : questions_reference_v2.csv (lecture seule ; sha256 0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083 avant et après la mesure).
- Configuration : src/demo/repondre.py --evaluer, règle figée (SEUIL_SCORE_MIN = 9,085). Une seule exécution.
- Résultats :
  - dans le périmètre (n = 34) : R@1 = 21/34 (inchangé) ; R@5 = 28/34 (contre 29/34 sans règle, car Q28 est désormais abstenue) ; abstention à tort = 3/34 (Q28, Q30, Q31 : tous les trois tunisiens) ;
  - hors périmètre (n = 6) : abstention = 1/6 (Q36 et Q37, Q38, Q40 non abstenues : le système renvoie un article).
- Comparaison : sans seuil, la démo n'abstenait jamais (0/34 faux, 0/6 correct). Avec le seuil : 1/6 hors abstenus pour 3 fausses abstentions. Le gain est donc négatif sur le test.
- Constat : la règle généralise mal. Les questions tunisiennes, en alphabet latin et peu lexicales, ont un score BM25 faible même lorsqu'elles sont dans le périmètre ; le seuil les refuse à tort. Une seule question tunisienne figurait dans le dev.
- Statut du test : ce jeu a maintenant servi à mesurer la règle. Il ne doit plus servir à en régler une autre. Toute nouvelle règle exige un nouveau jeu de test (v3) ou un nouveau jeu de développement.
- Limites : 6 questions hors périmètre seulement ; R@5 et abstention sont confondus par la règle.
- Décision et suite : ne pas modifier la règle sur le test. Prochaine étape : élargir le jeu de développement, surtout en tunisien et en hors périmètre, puis choisir une règle qui normalise le score par la longueur de la question ; la mesure finale se fera sur un nouveau test.

---

## 2026-10-27 — Élargissement du jeu de développement (data/dev/questions_dev_v2.csv) et nouveau choix de règle
- Objectif : élargir le dev, en particulier tunisien et hors périmètre, puis reprendre le choix de la règle d'abstention. Aucune mesure sur le test gelé.
- Composant / lot : RAG et abstention.
- Jeu utilisé : questions_dev_v2.csv (56 questions : 27 dans le périmètre, 29 hors périmètre ; sha256 9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8). questions_dev_v1.csv (28 questions) conservé sans modification. Les 28 nouvelles questions : articles 22, 79, 85, 122, 149, 160, 170, 191, 198, 216, 232 (FR et tunisien) et 15 hors périmètre (dont 2 tunisiennes et 2 arabes ; une arabe est hors périmètre). Pas de chevauchement avec test_locked.
- Configuration : script src/evaluation/choisir_regle_abstention.py (DEV = v2) ; règles comparées : A, B (couverture), C (score BM25 minimal), D (score BM25 par terme distinct). Tableau : data/dev/choix_regle_abstention_v2.csv.
- Résultats dev v2 :
  - règle A : 0 hors abstenu ;
  - règle B : 0 hors abstenu sans fausse abstention ;
  - règle C : 22/29 hors abstenus sans fausse abstention pour s = 8,75 et 8,93 (plage à départager, milieu ≈ 8,84) ;
  - règle D : 0 hors abstenu sans fausse abstention : la normalisation par le nombre de termes ne sépare pas les deux populations sur ce dev.
- Comparaison avec le dev v1 : la règle C avait retenu 9,085 sur v1 (13/15). Le seuil change donc de façon notable quand le dev change : le choix est instable.
- Décision : la règle C reste la seule candidate, avec un seuil proche de 8,84 à figer. La démo n'est pas modifiée dans cette entrée (le seuil 9,085 reste en place jusqu'à décision). Aucune mesure sur le test : pour mesurer ce choix, il faut un nouveau jeu de test (v3), écrit et gelé avant toute mesure.
- Limites : 56 questions de dev, rédigées par l'assistant ; les réponses FR ne sont pas vérifiées sur image ; la règle C reste sensible à la longueur et au vocabulaire de la question.
- Suite : créer test v3 (dans test_locked), le geler, puis mesurer la règle C figée à partir du dev v2.

---

## 2026-10-27 — Création et gel du test v3 (test_locked v3), avant toute mesure
- Objectif : disposer d'un jeu de test neuf pour mesurer la règle d'abstention choisie sur le dev v2, sans réutiliser le test v2 déjà consommé.
- Composant / lot : RAG et abstention.
- Jeu créé : data/test_locked/questions_reference_v3.csv, 40 questions : 20 dans le périmètre (16 FR, 4 tunisiennes) et 20 hors périmètre (dont 2 arabes et 2 tunisiennes). sha256 70fe347a198f22fe3ebb55f94bd9d08958329f581e7305e8f6b1fde40616b610.
- Sources : articles dont le texte a été lu sur les images de pages (articles 100, 103, 109, 111, 113, 114, 206, 207, 219, 220, 227, 261, 262, 300, 303, 417, 426). Aucun article ni aucune question en commun avec le test v2 ou le dev v2.
- Règle à mesurer (figée avant mesure) : règle C, abstention si le meilleur score BM25 est inférieur à 8,84 (milieu de la plage 8,75–8,93 du dev v2), en plus de la règle « aucun terme présent ».
- Résultats : aucune mesure faite à cette étape.
- Limites : les réponses de test v3 sont rédigées à partir des textes, dont les pages ont été lues ; les réponses tunisiennes doivent être relues par un locuteur tunisien.
- Suite : une seule mesure sur test v3 avec la règle figée ci-dessus ; la démo n'est pas modifiée avant cette mesure.

---

## 2026-10-27 — Mesure unique sur test_locked v3 avec la règle figée (seuil 8,84)
- Objectif : première mesure sur un jeu neuf de la règle d'abstention choisie sur le dev v2.
- Jeu utilisé : questions_reference_v3.csv (lecture seule ; sha256 70fe347a198f22fe3ebb55f94bd9d08958329f581e7305e8f6b1fde40616b610 avant et après la mesure). Gelé avant mesure (entrée précédente).
- Configuration : src/evaluation/mesure_test_v3.py ; règle figée : abstention si aucun terme présent dans le corpus, ou meilleur score BM25 < 8,84. Une seule exécution. La démo (src/demo/repondre.py, seuil 9,085) n'est pas modifiée.
- Résultats :
  - dans le périmètre (n = 20) : R@1 = 15/20 ; R@5 = 17/20 ; abstention à tort = 1/20 (R20, tunisienne) ;
  - hors périmètre (n = 20) : abstention = 13/20 (7 non abstenues : R22, R24, R25, R28, R29, R33 arabe, R34 tunisienne).
- Erreurs observées : R15 (article 303) et R17 (article 426) : bon article au rang 4 ou 2, faux premier rang ; R18 et R19 (tunisien) : article absent du top 5 ou premier rang erroné, lexique non apparenté ; R20 (tunisien, article 262) : abstention à tort ; les 7 hors périmètre non abstenus renvoient des articles à faible score, souvent par mots communs (« registre », « contrat », « délai », « accident »).
- Comparaison : sur ce jeu, la règle abstient 13/20 hors périmètre pour 1/20 fausse abstention, ce qui est nettement meilleur que la règle sans seuil (0/20).
- Limites : jeu de 40 questions, dont 20 dans le périmètre : un écart de 1 question change de 5 points ; les réponses tunisiennes ne sont pas relues ; le seuil a été choisi sur un dev de 56 questions et reste sensible à la longueur de la question.
- Statut du test : test v3 consommé pour cette règle. Toute nouvelle règle exige un test v4.
- Décision et suite : la démo peut recevoir le seuil 8,84 si vous validez ; la relecture tunisienne reste à faire ; les 7 hors périmètre non abstenus et l'erreur R20 sont des cas d'analyse pour la revue d'erreurs.

---

## 2026-10-27 — Décision : seuil de la démo maintenu à 9,085
- Décision de l'utilisatrice : la démo garde SEUIL_SCORE_MIN = 9,085 (valeur choisie sur le dev v1). Aucune modification de src/demo/repondre.py.
- Constat : le seuil 8,84 de la règle figée sur le dev v2 et mesurée sur le test v3 n'est pas appliqué. Le test v3 reste consommé pour la règle 8,84 ; la valeur 9,085 n'a pas été mesurée sur test v3 et ne doit pas l'être sans test v4.
- Limite : sur le test v3, le seuil 9,085 n'a pas de résultat mesuré ; la démo et la mesure ne sont donc pas alignées sur un même jeu neuf.
- Suite : toute mesure de 9,085 demande un nouveau test (v4).

---

## 2026-10-27 — Élargissement du dev (questions_dev_v3.csv) et choix de la règle d'abstention (option 2)
- Objectif : reprendre le choix de la règle sur un dev plus large, avant de créer un test v4 neuf. Aucun test lu.
- Jeu utilisé : data/dev/questions_dev_v3.csv (84 questions : 40 dans le périmètre, 44 hors périmètre ; sha256 dec1b6f606972e3c75364e3d69df4617f30986a8c435dc220129163336ccb1e4). Ajout : 13 dans le périmètre (articles 101, 102, 176, 224, 225, 229, 428, 429 en FR et 104, 210, 223, 101, 226 en tunisien) et 15 hors périmètre (dont 4 tunisiennes et 3 arabes).
- Configuration : src/evaluation/choisir_regle_abstention_v3.py ; règles A à F (aucune fausse abstention exigée sur le dev dans le périmètre). Tableau : data/dev/choix_regle_abstention_v3.csv.
- Résultats dev v3 (meilleur admissible par règle) :
  - A : 1/44 hors abstenu ; B : 1/44 ; D : 1/44 ; F : 0/44 ;
  - E (combinaison couverture et score) : aucun seuil sans fausse abstention ;
  - C (meilleur score BM25 < s) : 16/44 hors abstenus pour s ∈ ]7,46 ; 7,52] : retenue, milieu = 7,49.
- Constat : le seuil de la règle C a changé à chaque élargissement du dev (9,085 sur v1, 8,84 sur v2, 7,49 sur v3). La règle n'est donc pas stable. Son rendement sur hors périmètre reste faible (16/44 sur le dev v3).
- Décision : règle C, seuil 7,49, retenue pour une mesure sur un test v4 neuf. Non appliquée à la démo avant cette mesure.
- Suite : créer test v4 (articles différents des tests v2 et v3, autant que possible), le geler, puis mesurer une seule fois la règle C à 7,49.

---

## 2026-10-27 — Création, gel et mesure unique du test v4 (règle C, seuil 7,49)
- Objectif : mesurer une seule fois la règle choisie sur le dev v3, sur un test neuf.
- Jeu utilisé : data/test_locked/questions_reference_v4.csv, 40 questions : 20 dans le périmètre (12 FR, 7 tunisiennes, 1 ... voir ci-dessous), 20 hors périmètre (dont 4 tunisiennes et 3 arabes en comptant S37 à S40). sha256 fa15c794043717968c3d458688120d26f2ee634e2f2710b28f1241547fbbab34 avant et après la mesure.
- Articles : aucun en commun avec les tests v2 et v3 ; trois articles communs avec le dev v3 (104, 225, 226), posés avec d'autres questions. Articles lus sur image pour la plupart (110, 112, 129, 104, 169, 173, 209, 226, 298, 299, 301, 410).
- Règle mesurée (figée avant mesure) : abstention si aucun terme présent, ou meilleur score BM25 < 7,49. Script : src/evaluation/mesure_test_v4.py. Une seule exécution. Démo non modifiée.
- Résultats :
  - dans le périmètre (n = 20) : R@1 = 13/20 ; R@5 = 14/20 ; abstention à tort = 1/20 (S16, tunisienne) ;
  - hors périmètre (n = 20) : abstention = 12/20 (non abstenues : S25, S31 (FR), S33, S34, S35, S36 (tunisiennes), S38, S39 (arabes)).
- Erreurs observées : toutes les questions tunisiennes dans le périmètre (S13 à S19) ont pour premier résultat l'article 445, un article sans rapport. C'est un effet du vocabulaire mixte tunisien : les mots fonctionnels tunisiens (ken, chnowa, el, fel, kifech) ne sont pas dans la liste de mots vides, donc ils attirent le même article. Cette constatation ne doit pas servir à régler la règle sur le test v4.
- Comparaison : sur le test v3, la règle à 8,84 donnait 13/20 hors abstenus et 1/20 fausse abstention ; sur le test v4, la règle à 7,49 donne 12/20 et 1/20. Les deux seuils diffèrent, donc ce sont deux règles différentes.
- Limites : seulement 20 questions dans le périmètre ; les réponses tunisiennes ne sont pas relues ; le seuil dépend de chaque jeu.
- Statut : test v4 consommé pour la règle 7,49. Toute nouvelle règle exige un test v5.
- Suite : la démo n'est pas modifiée tant que la décision n'est pas prise. Piste pour le dev suivant (à valider sur dev, pas sur test) : étendre la liste de mots vides tunisiens, puis refaire le choix sur un nouveau dev.

---

## 2026-10-27 — Correction de la composition du test v4 (entrée précédente)
- Constat : l'entrée précédente indique « 12 FR, 7 tunisiennes, 1 ... » et « 4 tunisiennes et 3 arabes » ; ces comptes sont faux.
- Composition exacte (vérifiée sur le fichier) : dans le périmètre = 12 français (S01 à S12) et 8 tunisiennes (S13 à S20) ; hors périmètre = 12 français (S21 à S32), 4 tunisiennes (S33 à S36) et 4 arabes (S37 à S40).
- Les résultats mesurés ne changent pas : la mesure a été faite sur le fichier réel.
- sha256 du fichier : fa15c794043717968c3d458688120d26f2ee634e2f2710b28f1241547fbbab34 (inchangé).

---

## 2026-10-27 — Dev v4 : test des mots vides tunisiens et choix du seuil (aucun test lu)
- Objectif : décider si une liste de mots vides tunisiens améliore la règle C, sur un dev neuf (dev v4), avant tout test v5.
- Jeu utilisé : data/dev/questions_dev_v4.csv (96 questions : 48 dans le périmètre, 48 hors périmètre ; sha256 3cbacb17c7d8b8e3842422d2cdf7adcf68c966c5325f6d71d95deeddec27e14e). Ajout par rapport au dev v3 : 8 questions tunisiennes dans le périmètre et 4 tunisiennes hors périmètre.
- Configuration : liste STOP_TUN (ken, chnowa, chkoun, kifech, el, fel, mta3, 3la, fi, lazem…) appliquée côté requête seulement (corpus inchangé) ; flag ACTIVER_STOP_TUN ; script src/evaluation/choisir_regle_abstention_v4.py.
- Résultats dev v4 (règle C, 0 fausse abstention dans le périmètre) :
  - sans mots vides : 17/48 hors abstenus, seuil 7,46 (valeur unique admissible) ;
  - avec mots vides : 0/48 hors abstenus, et seuil admissible seulement 0 (ce qui ne refuse rien).
- Constat : sans mots vides, plusieurs questions tunisiennes dans le périmètre ont un score élevé (≈ 8,94) grâce au seul token « el », ce qui gonfle les scores et masque la séparation. Avec mots vides, plusieurs questions tunisiennes dans le périmètre n'ont plus aucun terme présent dans le corpus (score 0), donc refusées à tort : le problème est lexical (translittération), pas seulement une question de mots vides.
- Décision : variante sans mots vides retenue sur le dev v4 ; seuil 7,46. La liste STOP_TUN reste désactivée dans la démo.
- Décision : pas de test v5 pour l'instant. La règle retenue est quasi identique à celle mesurée sur le test v4 (7,49), donc une nouvelle mesure n'apporterait pas d'information nouvelle. Le vrai verrou est la translittération tunisienne, qui demande un composant à part, à concevoir sur dev.
- Limites : le « milieu de plage » du script ne vaut ici que pour une valeur unique ; le seuil 7,46 n'est pas stable d'un dev à l'autre (9,085 / 8,84 / 7,49 / 7,46).
- Suite : décision utilisatrice requise (translittération tunisienne sur dev, ou clôture de la question du seuil).

---

## 2026-10-27 — Décision : la démo reste à 9,085 (ni 8,84, ni 7,49, ni 7,46)
- Décision de l'utilisatrice : SEUIL_SCORE_MIN = 9,085 et ACTIVER_STOP_TUN = False dans src/demo/repondre.py.
- Les seuils choisis sur les dev v2, v3 et v4 (8,84 ; 7,49 ; 7,46) ne sont pas appliqués à la démo.
- Aucun test n'a été consommé pour cette décision.

---

## 2026-10-27 — Analyse des erreurs de la démo sur dev v4 (règle figée 9,085)
- Objectif : exigence du guide (au moins 30 erreurs, 4 à 6 catégories) pour le composant RAG et abstention.
- Jeu utilisé : questions_dev_v4.csv (96 questions, lecture seule). Aucun seuil modifié, aucun test lu.
- Configuration : src/evaluation/analyse_erreurs_bout_en_bout.py ; démo figée (SEUIL_SCORE_MIN = 9,085, mots vides tunisiens désactivés). Sortie : data/processed/erreurs_bout_en_bout_dev_v4.csv.
- Résultats : 27 erreurs sur 96 questions, réparties en 4 catégories :
  - 17 : score sous le seuil (abstention à tort, termes présents) ;
  - 6 : hors périmètre accepté (termes communs avec le Code) ;
  - 2 : article absent du top 5 ;
  - 2 : article voisin classé devant (rang 2 à 5).
- Écart au guide : 27 erreurs, il en faut au moins 30. Il manque 3 erreurs. Ajouter des questions de dev, ou inclure les erreurs des tests déjà mesurés à des fins d'analyse seulement (à décider).
- Limites : la catégorie « score sous le seuil » domine (17/27) et reflète le seuil 9,085, pas seulement la langue.
- Suite : compléter le dev ou décider de l'inclusion des erreurs de test pour atteindre 30.

---

## 2026-10-27 — Dev v5 et analyse des erreurs de la démo (règle figée 9,085)
- Objectif : atteindre au moins 30 erreurs pour l'analyse du composant RAG et abstention (exigence du guide).
- Jeu utilisé : data/dev/questions_dev_v5.csv (108 questions : 53 dans le périmètre, 55 hors périmètre ; sha256 107e3768fe099a12299ef6f55f485b88d32993caf586565ad82c352ecdfaae5a). Ajout par rapport au dev v4 : 5 questions tunisiennes dans le périmètre (articles 124, 140, 191, 232, 149), 5 françaises et 1 arabe hors périmètre, 1 tunisienne hors périmètre.
- Configuration : démo figée (SEUIL_SCORE_MIN = 9,085 ; mots vides tunisiens désactivés). Aucun seuil modifié, aucun test lu. Script : src/evaluation/analyse_erreurs_bout_en_bout.py ; sortie : data/processed/erreurs_bout_en_bout_dev_v5.csv.
- Résultats : 33 erreurs sur 108 questions, en 4 catégories :
  - 19 : score sous le seuil (abstention à tort) ;
  - 8 : hors périmètre accepté (termes communs avec le Code) ;
  - 4 : article voisin classé devant (rang 2 à 5) ;
  - 2 : article absent du top 5.
- Écart au guide : 33 erreurs, au-dessus du seuil de 30 ; 4 catégories, dans la fourchette 4 à 6.
- Limites : la catégorie dominante reste liée au seuil 9,085 ; les réponses des questions ajoutées ne sont pas vérifiées sur image (tunisien : relecture à faire).

---

## 2026-10-27 — Diapositives de la Revue Bronze (PDF, 12 pages)
- Objectif : livrable 1 du guide (diapositives PDF), pour la présentation Bronze.
- Fichiers : reports/revue_bronze/slides.html (source) et reports/revue_bronze/revue_bronze_slides.pdf (rendu Chromium, 12 pages au format 16:9).
- Contenu : carte du système, démo, données, quatre composants (OCR, alignement, BM25, abstention) avec extraits de code, résultats des jeux gelés, analyse des erreurs (dev v5), limites, reproduction.
- Chiffres repris de : data/processed/baseline_bm25_v2_resultats.csv, data/processed/erreurs_bout_en_bout_dev_v5.csv, experiments.md (entrées du 2026-10-27).
- Limites affichées dans le document : seuil instable, tunisien non traité, pas de kappa, pas de rappel sur l'alignement, test v2 mesuré trois fois.
- Suite : vidéo de secours (2 minutes), puis déclaration d'usage de l'IA et kanban.

## 2026-10-27 — Vidéo de secours de la Revue Bronze

- Objet : vidéo de secours de 2 minutes (guide : démo de bout en bout si la démo en direct échoue).
- Fichier : reports/revue_bronze/video_secours_bronze.mp4 (H.264, 1280×720, 118,3 s, 1,0 Mo, décodage complet sans erreur).
- Contenu : carte de titre, quatre questions réelles dans src/demo/repondre.py (préavis CDI, question en arabe, question hors périmètre sur le passeport avec abstention, question sur le salaire avec échec affiché : article 134 au lieu d'un article sur la rémunération), puis --evaluer sur questions_reference_v2.csv (R@1 21/34, R@5 28/34, abstention à tort 3/34, hors périmètre abstenu 1/6), carte « Reproduire ».
- Sorties : captures copiées telles quelles depuis les exécutions réelles (data/processed/demo_bout_en_bout_v2_resultats.csv pour la dernière ligne), aucune sortie inventée.
- Méthode : page HTML avec animation de terminal, enregistrement Playwright Chromium (webm), conversion ffmpeg en MP4.
- Limite : la vidéo montre un échec (salaire) et une question en arabe dont le 14 bis est second ; elle ne remplace pas une relecture tunisienne.
- Suite : déclaration d'usage de l'IA, kanban, fiches modèle par composant.

## 2026-10-27 — Test OCR / segmentation v1 (test_locked ocr v1) : gel, vérité terrain et mesure unique

- Objectif : donner au composant OCR / segmentation une métrique sur test fixe face à une baseline triviale (exigence du guide).
- Composant / lot : segmentation (notebook 02 v15) et corrections FR (notebook 04 v2).
- Jeu : 30 articles français tirés sans remise, graine 20261027, hors numéros déjà consultés (même exclusion que le test d'alignement). Script : `src/evaluation/tirage_test_ocr_v1.py`. Fichier gelé : `data/test_locked/ocr_candidats_v1.csv`, sha256 0969c1aa98193fb40c1c8d9989f3fa4599ec072f4e9eab3448b5d0a7fc927608.
- Baseline triviale gelée avant toute annotation : `data/test_locked/ocr_baseline_v1.csv`, sha256 f2be31a94d64886b313ec5a41f1d9dbcfc396d8a42126c1585417f2301cb59d3 (script `src/evaluation/baseline_ocr_brut.py`). Règle : première page PDF où une ligne commence par « Article N » suivi de « . », « - », « – », « — » ou « : ».
- Vérité terrain : `data/test_locked/ocr_gold_v1.csv`, page PDF où l'en-tête « Article N » est imprimé, lue sur l'image de chaque page (pages 148 à 280). Critère : la page citée est celle de l'en-tête.
- Résultats (mesure unique, `src/evaluation/mesure_test_ocr_v1.py`) :
  - pipeline (page_pipeline) : 29/30 = 96,7 % ;
  - baseline triviale : 18/30 = 60,0 %.
- Erreur du pipeline (1) : FR-14, page citée 277 (texte « Article 14 quinter ») au lieu de 279 (en-tête « Article 14.- »).
- Erreurs de la baseline (12) : pas de page trouvée pour 11 articles, et FR-151 apparié à la ligne « Article 151 - 2 » (page 227) au lieu de l'en-tête « Article 151 » (page 228). La règle ne reconnaît pas « Article N (Modifié … ) » : c'est une faiblesse de la baseline, pas une correction ; la règle reste celle gelée.
- Limites : critère limité à la page de l'en-tête (le texte intégral et l'absorption d'autres parties ne sont pas mesurés ici) ; une seule annotatrice (kappa non calculable) ; 30 articles ; la vérité terrain a été lue par l'assistant sur image et doit être validée par l'auteure avant présentation.
- Chevauchement : FR-76 et FR-233 font aussi partie du test d'alignement v1 ; les deux tests sont distincts et chacun est mesuré une fois.
- Décision et suite : métrique OCR = 96,7 % contre 60,0 % pour la baseline, présentée avec ces limites ; diapositive et fiche modèle à mettre à jour après validation de la vérité terrain.

## 2026-10-27 — Validation de la vérité terrain OCR (ocr_gold_v1.csv) et diapositive finale

- Validation par l'auteure : les 30 pages de référence (page PDF de l'en-tête « Article N ») sont confirmées. Le fichier `data/test_locked/ocr_gold_v1.csv` est désormais figé ; aucune ligne ne change.
- Résultat inchangé et définitif : pipeline 29/30 = 96,7 % ; baseline triviale 18/30 = 60,0 % (`data/processed/mesure_ocr_v1_resultats.csv`).
- Diapositive 4 mise à jour (PDF de 12 pages), avec la mention de validation.

## 2026-10-27 — Correction de 7 lignes de l'alignement (copie corrigée, fichier d'origine intact)

- Décision de l'auteure : corriger les 7 lignes signalées par la vérification du dev alignement v1 (`data/dev/alignement_dev_v1.csv`).
- Fichier d'origine `data/processed/alignement_fr_ar.csv` (sha256 36d70e01d582530a0390188b8a4b9d894fdd4754a7232656b0eacbba63a4e690) : non modifié.
- Copie corrigée : `data/processed/alignement_fr_ar_corrige_7.csv` (sha256 563edd40337f011af4c3ce1bd1ff29f75e70ce474e875b715a7b88f2df38ec06).
- Modifications (7 cellules) :
  - statut « apparié » → « abrogé (article) » : AR-50 / FR-50, AR-135 / FR-135 (abroge = True dans le fichier) ;
  - étiquette article_fr : FR-151 → FR-151-2 ; FR-152 → FR-152-2 ; FR-154 → FR-154-2 ; FR-376 → FR-376-ter ; FR-384 → FR-384-bis (texte et ligne FR vérifiés sur image).
- Constat en revue, non corrigé (en attente de décision) :
  - 69 paires appariées ont une clé suffixée mais une étiquette FR sans suffixe (les 5 ci-dessus en font partie) ;
  - 15 autres lignes ont abroge = True et statut « apparié » (dont AR-285 / FR-285, dev A039, que j'avais à tort validé comme statut correct).
- Limite : le notebook `03_alignement_fr_ar_v5.ipynb` n'a pas été modifié ; une relance écrasera la copie corrigée. La correction définitive doit se faire dans le notebook.
- Le test d'alignement v1 (`data/test_locked/`) n'est pas modifié.

## 2026-10-27 — Décision : pas de correction des 84 lignes restantes de l'alignement

- Décision de l'auteure : garder la copie corrigée à 7 lignes (`data/processed/alignement_fr_ar_corrige_7.csv`) ; aucune autre ligne n'est modifiée.
- Défauts connus, non corrigés, à annoncer comme limite : 69 étiquettes FR sans suffixe pour des paires à clé suffixée ; 15 lignes abrogées (abroge = True) marquées « apparié ».
- Fichier d'origine `data/processed/alignement_fr_ar.csv` et test d'alignement v1 : non modifiés.

## 2026-10-27 — Exigences du cahier et du guide pour l'alignement : extension du jeu à annoter par l'auteure

- Exigences retenues : cahier des charges, section 9 (précision ET rappel de l'alignement ; au moins 30 erreurs catégorisées par composant) et section 10 (interdiction de fabriquer des annotations « humaines » ou des références non lues).
- Constat : les 60 verdicts de `data/dev/alignement_dev_v1.csv` ont été saisis par l'assistant. Ils ne sont pas validés par l'auteure. La déclaration d'usage de l'IA a été corrigée en conséquence.
- Action : tirage de 100 paires appariées supplémentaires (graine 20261029, hors test v1 et hors dev v1), sans verdict pré-rempli : `data/dev/alignement_dev_v2_a_annoter.csv`. Ces paires doivent être annotées par l'auteure sur les images.
- Non fait : le rappel de l'alignement (il exige un gold sur des articles sans appariement) ; la validation des verdicts v1.

## 2026-10-27 — Mise à jour des documents sur l'état de l'alignement (sans nouvelle mesure)

- Diapositive 5, fiche `model_cards/02_alignement_fr_ar.md` et kanban : ajout des défauts connus (69 étiquettes FR sans suffixe, 15 lignes abrogées marquées « apparié »), de la copie corrigée à 7 lignes, et du tirage de 100 paires à annoter.
- Aucune nouvelle mesure ; le rappel reste non mesuré ; les 60 verdicts de dev v1 restent non validés.
- PDF des diapositives recompilé (12 pages).

## 2026-10-27 — Statut final de la Revue Bronze (document de clôture)

- Document : `reports/revue_bronze/statut_final_revue_bronze.md`. Il liste le livré, les points ouverts à la charge de l'auteure, les exigences du cahier non traitées pour le Bronze, et les limites à dire en revue.
- Ouvert : 30 erreurs d'alignement (7 défauts relevés), rappel de l'alignement, 100 paires à annoter, validation des 60 verdicts de dev v1, réponses arabes sur image, relecture tunisienne, décision sur 84 lignes.
- Aucun commit ni tag.

## 2026-10-27 — Rappel de l'alignement : tirage à l'aveugle (sans mesure)

- Objet : mesurer le rappel exigé par le cahier (section 9). Le rappel ne peut pas se mesurer sur les paires candidates (la précision l'a déjà été) : il faut un gold indépendant de l'algorithme.
- Méthode retenue : tirage de 60 articles arabes (graine 20261030) hors dev v1, dev v2 et test v1 ; fichier `data/dev/rappel_a_annoter_v1.csv`. La sortie de l'algorithme n'y figure pas : l'auteure cherche l'article français équivalent dans le texte, puis on compare avec l'alignement.
- Pas de mesure faite. Pas de verdict saisi par l'assistant.
- Limite de la méthode : si le tirage tombe surtout sur des articles sans équivalent, le rappel sera peu informatif ; le nombre de paires vraies dans l'échantillon sera donné après annotation.

## 2026-10-27 — Réponses arabes du jeu v1 : validation par l'auteure

- L'auteure a relu sur image les réponses arabes du jeu de questions v1 (8 questions dans le périmètre). Les lectures préparatoires faites par l'assistant (entrée du même jour) sont recoupées par cette relecture.
- Mises à jour : déclaration d'usage de l'IA (section 4), kanban, statut final : la mention « à confirmer » est retirée.
- Fichier gelé `questions_reference_v1.csv` non modifié.

## 2026-10-27 — Contrôle d'identité du PDF source (validé par l'auteure)

- Objet : vérifier que le PDF joint par l'auteure est le même fichier que celui du projet.
- Fichier joint : `fa248eb4-majallat_al_shougl_2019_1.pdf` ; fichier du projet : `data/raw/arabic/majallat_al_shughl_2019.pdf`.
- Résultat : identiques. SHA-256 `de17529ea734212b6efcec0d796762f39fefbf97455a573ca402bf83c74bc467`, 1 170 023 octets, 291 pages.
- Limite : contrôle de l'empreinte du fichier entier, pas relecture du contenu page par page.
- Validé par l'auteure le 27 octobre 2026.
- Correction de nom dans l'entrée ci-dessus : le fichier joint s'appelle `fa248eb4-majallat_al_shughl_2019_1.pdf` (la graphie « shougl » est une coquille ; le contrôle porte sur le contenu, pas sur le nom).

## 2026-10-27 — Alignement : 100 paires de dev v2 annotées par l'auteure (dictée)

- Fichier : `data/dev/alignement_dev_v2_a_annoter.csv` (paires B001–B100, tirées du jeu apparié, graine 20261029, hors dev v1 et test v1).
- Verdicts : dictés par l'auteure. B001–B003 saisis ligne par ligne ; B004–B100 dictés en bloc comme « correct ». Remarque « correcte » pour toutes les lignes sauf celles à catégorie.
- Résultat : 100 verdicts « correct », 0 erreur d'appariement.
- Catégories de défauts de métadonnées (verdict inchangé, correct) :
  - étiquette sans suffixe (appariement correct) : 10 lignes (B001, B002, B022, B023, B024, B034, B039, B041, B091, B094) ;
  - statut abrogé non signalé : 2 lignes (B017, B069).
- Lecture de ce résultat : ces 100 paires ne donnent aucune erreur d'appariement. Le critère du cahier (au moins 30 erreurs catégorisées) n'est pas atteint par ce jeu. Aucune nouvelle mesure n'a été faite ; le rappel n'est pas mesuré.
- Limite : les 97 verdicts dictés en bloc n'ont pas été relus ligne par ligne par l'assistant ; ils sont enregistrés tels que dictés par l'auteure.

## 2026-10-27 — Verdicts de dev v1 : validation par l'auteure (A001 à A020)

- Fichier : `data/dev/alignement_dev_v1.csv`, nouvelle colonne `validation_auteure` ajoutée (les verdicts d'origine, saisis par l'assistant, ne sont pas modifiés).
- Validés par l'auteure : A001 à A020, verdicts inchangés. A007 et A016 gardent « correct_mais_statut_incomplet » (statut abrogé non signalé).
- Restent non validés : A021 à A060 (40 lignes).
- Aucune nouvelle mesure.

## 2026-10-27 — Verdicts de dev v1 : validation par l'auteure (A021 à A060)

- Fichier : `data/dev/alignement_dev_v1.csv`, colonne `validation_auteure`.
- Validés par l'auteure : A021 à A060, verdicts inchangés. A039 garde « correct_mais_statut_incomplet » (statut abrogé non signalé). A021, A023, A024, A050 et A051 gardent leur catégorie « étiquette sans suffixe (appariement correct) ».
- Dev v1 validé en entier : 60 lignes sur 60 (A001 à A020 puis A021 à A060).
- Aucune nouvelle mesure.

## 2026-10-27 — Lot B (obligations) : exploration des formulations dans le corpus FR (sans mesure, sans annotation)

- Source : `data/processed/articles_fr_corrige.csv` (498 entrées, colonne `texte_fr`), lecture seule.
- Comptages de marqueurs (expressions régulières, première exploration) :
  - « doit / doivent » : 174 occurrences dans 116 articles ;
  - « tenu(s) de » et formes apparentées : 71 occurrences dans 59 articles (le motif inclut aussi des mots sans rapport, à filtrer) ;
  - « ne peut / ne peuvent / ne doit / ne doivent » : 88 occurrences dans 77 articles ;
  - « obligatoire / obligation » : 37 occurrences dans 34 articles ;
  - « interdit » : 11 occurrences dans 10 articles ;
  - « il incombe / il appartient » : 7 occurrences ; « l'obligation de » : 7 occurrences.
- Limite : ces comptages ne disent pas quelles occurrences sont des obligations. « Doit » peut décrire un fait, pas une obligation.
- Aucune annotation, aucune mesure. Les gold d'obligations seront saisis par l'auteure (cahier, section 10).

## 2026-10-27 — Lot B : modèle d'annotation des obligations (vide, sans annotation)

- Fichiers : `data/dev/obligations_guide_annotation_v1.md` (guide : définition, champs qui / modal / quoi / quand, règles de saisie, découpage 200 dev + 100 test) et `data/dev/obligations_modele_v1.csv` (en-tête seul, aucune ligne).
- Aucune obligation annotée. Les exemples du guide sont des schémas, non tirés du corpus.
- Décision à confirmer : valeurs de `modal` (obligation / interdiction / permission) et découpage dev 200 / test 100.
- Limite : un seul annotateur, kappa non calculable.

## 2026-10-27 — Lot B : choix du modèle d'annotation validés par l'auteure

- Valeurs de `modal` (obligation / interdiction / permission) et découpage dev 200 / test 100 : validés par l'auteure.
- Guide mis à jour sur ce point (`data/dev/obligations_guide_annotation_v1.md`). Modèle CSV inchangé, toujours vide.
- Aucune annotation, aucune mesure.

## 2026-10-27 — Lot B : échantillon de dev (phrases candidates, sans annotation)

- Fichier : `data/dev/obligations_candidats_dev_v1.csv` (200 lignes, identifiants D001–D200), colonnes du modèle `obligations_modele_v1.csv`. Seule la colonne `phrase` est remplie.
- Tirage : graine 20261031, parmi 319 phrases françaises contenant un marqueur lexical (doit, doivent, tenu, interdit, ne peut, obligatoire, obligation, incombe, appartient, défendu). Les phrases sont découpées sur les points et les points-virgules, longueur 25 à 400 caractères.
- Ce n'est pas une annotation : la phrase peut ne pas être une obligation. Le choix revient à l'auteure.
- Limite : le repérage lexical manque les obligations sans ces marqueurs. Le test gelé (100) sera tiré dans les 119 phrases restantes, pour rester disjoint du dev.

## 2026-10-27 — Test v4 : vérification sur la machine de l'auteure (sans nouveau résultat)

- Sur la machine de l'auteure (Windows, environnement `.venv`), `src/evaluation/mesure_test_v4.py` a été exécuté une fois, selon l'auteure.
- Sortie : dans le périmètre (n = 20) R@1 = 13/20, R@5 = 14/20, abstention à tort = 1/20 ; hors périmètre (n = 20) abstention = 12/20. Identique à l'entrée du 27 octobre (test v4 consommé pour la règle 7,49).
- Hash de `questions_reference_v2.csv` identique au journal (0015db2c…). La baseline BM25 et l'analyse dev v5 reproduisent les résultats enregistrés.
- Le test v4 reste consommé. Aucune nouvelle mesure n'est autorisée sur ce jeu.

## 2026-10-27 — Corrections avant publication du dépôt (sans nouvelle mesure)

- `PIPELINE.md` : mis à jour (date 27 octobre ; section 4 réécrite). Les mentions « src/ est vide », « data/test_locked/ est vide » et « pas de point d'entrée » étaient fausses et sont retirées.
- Tests : `tests/test_evaluation.py` ajouté. 6 tests passent, 1 test attendu en échec (`xfail` strict) : le sigle « CDI » est une limite connue. Les tests ne lancent aucune mesure sur un jeu gelé ; ils vérifient les sha256 des trois jeux gelés consignés (questions v2, OCR candidats v1, OCR baseline v1).
- Dossiers vides supprimés dans `src/` : alignment, api, ingestion, linguistic_analysis, preprocessing, rag, retrieval. `src/obligation_extraction/` conservé (lot B) avec un `.gitkeep`.
- Script de démo : `demo_evaluation.sh` ajouté à la racine (commandes sans mesure sur jeu gelé).

## 2026-10-27 — Reprise locale : récupération partielle et contrôles de fichiers

- Objectif : récupérer les fichiers fournis sans reconstruire les traitements manquants ni modifier les annotations.
- Copie initiale : 10 fichiers, identiques à l'archive `LegalTN.zip`, sans `.git`. Les sources et les 36 tests signalés dans le compte rendu Codex sont absents.
- Fichiers récupérés à l'identique : `texte_travail.json`, `articles_fr.csv`, `articles_fr_corrige.csv`, `questions_dev_v2.csv`, `01_data_exploration.ipynb` et `Guide_Revue_Bronze.pdf`. Emplacements et empreintes dans `PROJECT_PROGRESS.md` et `reports/reprise/audit_donnees_recuperees.json`.
- Configuration : Python 3.12.2 ; `python src/auditer_reprise.py`, bibliothèque standard, lecture seule. Notebook non exécuté ; aucun jeu de test utilisé.
- Constats structurels : texte de travail de 291 pages (page 136 vide) ; 498 entrées dans chaque corpus FR, 425 identifiants distincts, 34 textes modifiés entre versions, ordre et métadonnées article/numéro/page conservés.
- Les références `fr_ligne` des 60 paires dev v1 et 100 paires dev v2 retrouvent toutes les identifiants/pages attendus. Ce n'est pas une mesure de justesse AR/FR.
- Questions dev v2 : 56 questions (27 dans le périmètre, 29 hors périmètre ; 44 FR, 9 tunisiennes, 3 AR). SHA-256 conforme à l'entrée historique : `9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8`.
- Obligations : 199/200 phrases candidates sont des extraits continus retrouvés de manière unique dans leur article/page du corpus corrigé. D045, FR-341 p. 179, est interrompue par une note éditoriale dans la version corrigée. Ce contrôle ne détermine pas si les phrases sont des obligations ; champs d'annotation laissés vides.
- Vérification syntaxique : 16 cellules de code du notebook analysées, aucune erreur de syntaxe. Les sorties enregistrées du notebook restent historiques.
- Tests applicatifs : tentative avec pytest 9.2.0 dans un environnement temporaire ; sortie 2, erreur de collecte `ModuleNotFoundError: baseline_bm25`. Aucun test exécuté. Démo : sortie 2, fichier `src/demo/repondre.py` absent.
- Limites : PDF original, corpus AR segmenté, notebooks 02/03/04, scripts Codex et jeux gelés absents. Tesseract disponible mais seulement avec `eng` et `osd`, sans `ara`/`fra`. Aucun résultat scientifique de modèle nouvellement mesuré ni annotation humaine créée.
- Suite : récupérer les sources originales et les corrections de segmentation, vérifier les trois modifications refusées, puis reprendre les traitements et l'évaluation. Ne pas transformer ce jeu de développement en test indépendant.

## 2026-10-27 — Reprise de l'alignement : notebooks récupérés, contrôle dev et exports protégés

- Objectif : reprendre les règles existantes sans reconstruire le corpus arabe absent ni écraser les fichiers historiques.
- Sources : `03_alignement_fr_ar.ipynb`, v4 et v5 récupérés à l'identique dans `notebooks/`. Empreintes dans `PROJECT_PROGRESS.md` et `reports/reprise/audit_alignement_v5.json`. La v5 est la référence du pipeline historique.
- Différences vérifiées : v4 reconnaît « Article premier » et exclut les pages 288–289 ; v5 utilise le CSV français corrigé en priorité.
- Configuration : Python 3.12.2, pandas 2.2.2 ; fonctions de normalisation originales v5 exécutées sans les cellules de chargement/export. Corpus FR corrigé et références dev v1/v2 héritées ; aucun jeu gelé utilisé.
- Contrôles : 494 clés FR distinctes dans le Code après exclusion de 4 entrées, aucune clé non reconnue/ambiguë ; lignes françaises attendues retrouvées pour 60 références dev v1 et 100 références dev v2. Ce contrôle ne mesure pas le rappel global et n'est pas un résultat de test indépendant.
- Correction opérationnelle : nouvelle version `03_alignement_fr_ar_v6.ipynb`, avec règles de calcul v5 conservées, repérage de racine sans `data/raw/`, sorties `_v6` et refus d'écrasement des exports existants. La v5 originale reste intacte.
- Tests : `python -m unittest discover -s tests -p test_alignement_notebook.py -v` ; 10 tests exécutés et réussis (0,178 s). Fixtures synthétiques pour suffixes, promulgation, ambiguïtés, absences, années et unicité ; contrôles de conservation des règles et de protection des exports. Aucune fixture n'est une annotation humaine ou un résultat du corpus.
- Audit : `python src/auditer_reprise.py`, sortie 0 ; JSON archivé dans `reports/reprise/audit_alignement_v5.json`.
- Limites : notebook complet non exécuté sur les données réelles, `articles_ar.csv` absent. Aucun alignement réel exporté. Les 36 tests Codex et les corrections refusées dans ses scripts restent invérifiables.
- Suite : récupérer le corpus arabe segmenté et vérifier sa provenance avant l'exécution de la v6 ; garder les étiquettes/statuts historiques comme limites tant qu'une correction sourcée n'est pas disponible.

## 2026-10-27 — Corpus AR récupéré : alignement complet et reproduction technique

- Objectif : exécuter l'alignement existant sur les vrais corpus, sans régénérer les données ni réécrire les annotations.
- Récupération : export `data-20261027T220600Z-1-001/data`, 728 fichiers dont 725 nouvellement copiés et 3 déjà identiques. Manifeste SHA-256 : `reports/reprise/recuperation_data_manifest.json`. Vérification après exécution : les 728 fichiers récupérés sont inchangés.
- Corpus AR : 515 lignes ; SHA-256 `77fe24b3d3ffc5923fd42fe4298521ebdbcec5f7af001ccd576a90fa69846022`. Aucun identifiant dupliqué, aucun numéro absent entre 1 et 446, aucun chapitre vide. PDF original récupéré, 291 pages, empreinte identique à celle consignée plus haut (`de17529e…`).
- Configuration : notebook v6 (règles de calcul identiques à v5), lancé par `src/executer_alignement.py` ; Python 3.12.2, pandas 2.2.2, NumPy 2.4.1. Corpus FR corrigé de 498 entrées. Graine 2026 pour l'échantillon de contrôle.
- Commandes exécutées avec sortie 0 : `python src/executer_alignement.py`, puis `python src/executer_alignement.py --sortie reports/reprise/reproduction_v6`.
- Résultat structurel : 519 lignes exportées, dont 494 appariées, 21 classées « abrogé (plage) », 4 hors Code ; zéro doublon à trancher, zéro absence du français. Six contrôles d'années : AR-18, AR-52, AR-335, AR-364, AR-417, AR-419. Le nombre de 3 contrôles mentionné dans le bilan historique du pipeline n'est pas reproduit.
- Reproduction : les trois fichiers exportés lors des deux exécutions sont identiques octet par octet. Rapport complet : `reports/reprise/audit_alignement_complet.json`.
- Comparaison historique : positions, clés, identifiants/pages, lignes FR et statuts inchangés sur les 519 lignes de l'ancien export. Huit lignes diffèrent dans les champs auxiliaires : six débuts de texte FR corrigés et déplacement d'une alerte d'année d'AR-367 vers AR-364, cohérent avec la note déplacée dans le corpus.
- Contrôle dev : l'export réel concorde avec les 60 références v1 et 100 références v2 héritées. Aucun jeu indépendant utilisé ; précision, rappel et F1 sur test indépendant non mesurés.
- Anomalies conservées : 69 étiquettes FR sans suffixe ; 17 paires à drapeau AR abrogé mais statut d'appariement « apparié » ; AR-367 a une longueur stockée de 362 pour 190 caractères. Les 39 lignes du fichier de notes récupéré comprennent encore 30 statuts de rattachement à effectuer ; ne pas présenter ce fichier comme preuve de clôture de toutes les notes.
- Tests réellement lancés : pytest 9.2.0 avec `--continue-on-collection-errors`, résultat `10 passed, 1 error, 6 subtests passed in 1.10s`, sortie 1. L'ancienne suite ne se collecte pas car `baseline_bm25.py` manque. Les 36 tests Codex ne sont pas confirmés.
- Limites : reproductibilité technique établie pour l'alignement, pas validation juridique ou évaluation indépendante. Pas de nouvelles annotations humaines. Les sources BM25/API, scripts Codex, jeux gelés et notebooks de segmentation/correction restent absents.
- Suite : récupérer les sources BM25/démo et les jeux gelés pour relancer les tests applicatifs ; retrouver les notebooks 02/04 pour tracer les transformations avant de corriger les anomalies héritées.

## 2026-10-27 — BM25 et démo restaurés, adaptateur HTTP et contrôle dev v2

- Objectif : reprendre la démo existante et vérifier les livrables réalisables sans les jeux de test gelés.
- Sources récupérées à l'identique : `src/evaluation/baseline_bm25.py` (sha256 `97adc260105f42f47b6ee7fb6cdba0d18bc27926a18df58219f2cb9face25588`) et `src/demo/repondre.py` (`ce84affd5943b92eb8cc0c19199a5d020dc849efae8a06715b396c3e3ab25b9c`).
- Configuration inchangée : BM25 k1=1,5, b=0,75 ; seuil 9,085 ; mots vides tunisiens désactivés. Démo CLI exécutée : préavis complet → 14 bis p. 279 ; capitale → abstention ; sigle CDI → fausse abstention connue.
- Ajouts locaux : `api.py`, `demarrer.ps1`, `tests/test_api.py`, adaptateur autour de la démo récupérée, distinct de l'API Codex non récupérée. Démarrage PowerShell et requêtes HTTP réellement vérifiés sur 127.0.0.1:18765 ; réponses dans `reports/reprise/verification_http.json`. Serveur de vérification arrêté ensuite.
- Jeu de contrôle : `data/dev/questions_dev_v2.csv`, empreinte historique vérifiée, 56 questions dont 27 dans le périmètre et 29 hors. Références héritées, aucune nouvelle annotation, aucun test gelé lu.
- Script : `src/evaluation/evaluer_dev_reprise.py --rapports reports/reprise/demo_dev`. Comparaison sans seuil de score / seuil historique sur le même classement, sans réglage.
- Résultats dev : article top1 correct 21/27 dans les deux variantes ; article dans top5 23/27 sans seuil, 21/27 avec seuil ; hors périmètre refusé 0/29 puis 27/29 ; fausses abstentions 0/27 puis 4/27.
- Erreurs : 35 sans seuil, 8 avec seuil, soit 27 évitées selon le critère « hors périmètre accepté, abstention à tort ou premier article incorrect ». Les quatre fausses abstentions remplacent des premiers résultats déjà erronés ; ne pas conclure que le seuil n'a aucun coût. Deux réussites top5 sont perdues.
- Catégories : quatre catégories automatiques au total entre variantes, trois non vides par variante. Le CSV des erreurs contient 43 observations variante/question, pas 43 erreurs indépendantes. Les questions AR sont toutes hors périmètre (3), donc aucun rappel arabe calculable.
- Livrables : JSON détaillé et trois tableaux CSV dans `reports/reprise/demo_dev/`, explicitement marqués développement non indépendant. Résultats du calcul reproduits à l'identique. Ils ne remplacent pas les tableaux finaux sur test ni le bilan Codex 30/21/9.
- Tests finaux de cette étape : `python -m pytest -q -p no:cacheprovider`, 20 réussis, 1 xfail, 1 échec, 17 sous-tests réussis, 2,32 s. L'échec concerne le fichier gelé `questions_reference_v2.csv` absent. Le contrôle reste actif.
- Limites observées : la démo indexe 496 lignes FR et 491 AR ; fonctions d'intitulé plus limitées que l'alignement (premier, sous-articles et certains suffixes). Détails dans `reports/reprise/restauration_demo_manifest.json`. Les 728 fichiers de données et les deux scripts récupérés sont inchangés.
- Suite : récupérer les jeux gelés et vérifier leurs empreintes, sans les utiliser pour calibrer ; poursuivre la récupération des composants obligations/NER/CoNLL et du cahier des charges complet.

## 2026-10-27 — Récupération des fichiers gelés et résolution du test d'intégrité

- Objectif : restaurer les fichiers attendus par les tests, sans relancer les mesures sur test.
- Fichiers récupérés à l'identique dans `data/test_locked/` : `questions_reference_v2.csv` (40 lignes, sha256 `0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083`), `ocr_candidats_v1.csv` (30 lignes, `0969c1aa98193fb40c1c8d9989f3fa4599ec072f4e9eab3448b5d0a7fc927608`) et `ocr_baseline_v1.csv` (30 lignes, `f2be31a94d64886b313ec5a41f1d9dbcfc396d8a42126c1585417f2301cb59d3`).
- Contrôles : empreintes conformes au journal et aux tests, structure CSV valide, aucune donnée modifiée. Manifeste : `reports/reprise/recuperation_jeux_geles.json`.
- Commande réellement exécutée : `python -m pytest -q -p no:cacheprovider` avec Python 3.12.2, pytest 9.2.0.
- Résultat logiciel : `21 passed, 1 xfailed, 17 subtests passed in 2.60s`, sortie 0. Le xfail strict reste le cas CDI connu. Le test des empreintes est inchangé et passe désormais.
- Aucune nouvelle mesure sur les jeux gelés ; aucun nouveau résultat scientifique ni annotation. Les gel et usages historiques ne sont pas réinitialisés. Les 36 tests Codex ne sont pas confondus avec les 22 tests présents.
- Limites : `ocr_gold_v1.csv`, la référence indépendante de rappel d'alignement, les annotations d'obligations et les sources NER/CoNLL restent absents. Les trois fichiers récupérés ne suffisent pas à déclarer ces composants évalués.
- Suite : poursuivre la récupération et l'audit des composants scientifiques manquants et du cahier des charges complet ; conserver la séparation entre validation logicielle et évaluation indépendante.

## 2026-11-15 — Silver, chantier 2 : recherche dense et hybride sur le dev v2 (aucun test lu)

- Objectif : comparer BM25, un encodeur multilingue pré-entraîné et leur fusion, sans aucun réglage.
- Code : `src/retrieval/dense.py`, `src/retrieval/hybride.py`, `src/evaluation/evaluer_retrieval.py` ; tests `tests/test_retrieval_hybride.py`.
- Configuration : `intfloat/multilingual-e5-base` (préfixes query:/passage:, troncature 512 jetons), sentence-transformers 6.3.0, torch 2.15.0+cpu, transformers 5.23.0, Python 3.11.9, CPU. Fusion RRF k=60 (valeur de l'article d'origine, non réglée). Graine torch 2026 (encodage déterministe, pas d'entraînement).
- Jeu : `data/dev/questions_dev_v2.csv` (sha256 9c616a6c…, vérifié par le script ; le script refuse `data/test_locked/`). 27 questions dans le périmètre : 21 FR, 6 « tun », 0 AR.
- Commande : `.venv/Scripts/python.exe -X utf8 src/evaluation/evaluer_retrieval.py --rapports reports/silver/retrieval_dev`. Index : 351,6 s ; 0,214 s par question.
- Contrôle : la ligne BM25 reproduit le contrôle du 2026-10-27 sans seuil (R@1 21/27, R@5 23/27).

| Langue (n dans périmètre) | BM25 R@1 / R@5 | Dense même langue | Dense croisé FR+AR | Hybride RRF |
|---|---|---|---|---|
| Toutes (27) | 21 / 23 | 21 / 22 | 21 / 22 | 21 / 21 |
| FR (21) | 20 / 21 | 21 / 21 | 21 / 21 | 21 / 21 |
| tun (6) | 1 / 3 | 0 / 1 | 0 / 1 | 0 / 0 |
| AR (0) | non mesurable | — | — | — |

- Lecture : en FR, le dense corrige la seule erreur top-1 de BM25 (20 → 21/21). Sur les 6 questions « tun », toutes écrites en caractères latins avec chiffres (arabizi), l'encodeur échoue et la fusion fait pire que BM25 (R@5 0/6 contre 3/6). Au total, l'hybride n'améliore pas BM25 sur ce dev (R@5 21 contre 23).
- Limites : effectifs minuscules (1 question d'écart = 4 points sur 27, 17 points sur 6) ; aucune conclusion statistique possible. Aucune question AR dans le périmètre. La catégorie « tun » du dev est en fait de l'arabizi. Abstention non traitée ici (les scores maximaux sont enregistrés pour un choix ultérieur sur dev).
- Sorties : `reports/silver/retrieval_dev/resultats.json`, `resume_par_langue.csv` (marqués développement non indépendant).
- Suite : questions AR/tunisien en écriture arabe/arabizi écrites par l'équipe (dev v3) ; ne pas choisir la configuration finale sur 27 questions.

## 2026-11-15 — Silver, chantier 4 : RAG avec LLM local, comparaison de 4 prompts sur le dev v2 (aucun test lu)

- Objectif : mesurer l'apport des passages retrouvés et du format de prompt sur la citation, les articles inventés et l'abstention.
- Code : `src/rag/rag.py`, `src/evaluation/evaluer_rag.py` ; tests `tests/test_rag.py` (sans appel au LLM).
- Configuration : Ollama 0.40.16, `qwen2.5:3b` (Q4_K_M) en local sur GTX 1650 ; température 0, seed 2026, num_ctx 8192, num_predict 400. Récupération : BM25 langue détectée, top-3, sans seuil ; textes FR + AR fournis, tronqués à 1 500 caractères chacun.
- Variantes : P0 LLM seul sans passage ; P1 RAG zéro-shot réponse libre ; P2 RAG + JSON imposé + règle d'abstention ; P3 = P2 + 2 exemples few-shot (D01, D14) ; P2V = P2 + rejet de toute réponse sans citation ou citant un article non fourni.
- Jeu : dev v2 (sha256 9c616a6c…), D01 et D14 exclus pour toutes les variantes → 26 dans le périmètre (20 FR, 6 tun), 28 hors (22 FR, 3 tun, 3 AR). Durée : 1 303 s. Premier lancement interrompu par un délai dépassé (génération non bornée) : corrigé par num_predict/num_ctx puis relancé en entier ; seul le second lancement est rapporté.
- Commande : `.venv/Scripts/python.exe -X utf8 src/evaluation/evaluer_rag.py --rapports reports/silver/rag_dev`.

| Variante | Citation exacte (dans, n=26) | Fausses abstentions | Hors périmètre refusé (n=28) | Citations non fournies |
|---|---|---|---|---|
| P0 LLM seul | 0 | 0 | 0 | 37 (aucun passage fourni) |
| P1 RAG libre | 20 | 0 | 0 | 0 |
| P2 RAG JSON | 18 | 2 | 26 | 0 |
| P3 few-shot | 19 | 1 | 22 | 3 |
| P2V vérifié | 18 | 3 | 26 | 0 |

- Par langue (citation exacte) : FR P0 0/20, P1 18/20, P2 16/20, P3 17/20, P2V 16/20 ; tun 0/6, 2/6, 2/6, 2/6, 2/6. AR : 0 question dans le périmètre (non mesurable) ; les 3 AR hors périmètre sont refusées par P2, P3, P2V.
- Lecture : sans passages (P0), le modèle ne cite jamais le bon article et cite 37 numéros non justifiés (existant dans le corpus, mais non pertinents) : c'est l'argument pour le RAG. P1 cite le mieux mais ne s'abstient jamais (0/28). P2 obtient l'abstention (26/28) au prix de 2 bonnes réponses perdues. Le few-shot (P3) n'aide pas l'abstention (22/28) et réintroduit 3 citations non fournies. P2V supprime toute citation non fournie par construction et coûte une fausse abstention de plus.
- Points de comparaison : la démo BM25 + seuil 9,085 refuse 27/29 hors périmètre sur le dev v2 complet (jeux légèrement différents : D01/D14 inclus).
- Limites : effectifs très faibles ; un seul modèle (3B) et une seule graine ; « citation exacte » ne dit rien de la justesse de la réponse rédigée (fidélité non évaluée : grille humaine à faire par l'équipe) ; extraction des citations de P0/P1 par expression régulière (« article N », « الفصل N ») ; plafonné par la récupération BM25 top-3.
- Sorties : `reports/silver/rag_dev/resultats.json` (toutes les sorties brutes), `reports/silver/rag_dev_log.txt`.
