# LegalTN — Section Gold du rapport (audit et transfert, W12)

> Brouillon du 22 novembre 2026. Tous les chiffres viennent de `experiments.md` (entrées du 22/11) et des fichiers de `reports/gold/`. Mesures sur des jeux de **développement** : le jeu `test_locked` n'a pas encore été mesuré.

## 1. Objectifs Gold et couverture

| Exigence (PDF du module) | Statut | Section |
|---|---|---|
| Transfert vers le tunisien mesuré | Fait | 3 |
| Abstention (par langue) | Fait | 3, 4 |
| Audit des hallucinations | Fait | 4 |
| Biais entre langues, robustesse INV | Fait (petits effectifs) | 5 |
| Au moins une question de recherche | Deux traitées | 6, 7 |
| LLM-juge validé | Partiel : non validé contre un humain | 8 |
| Divergences AR / FR détectées et évaluées | Détecteur fait, évaluation humaine à faire | 9 |
| Explications | Extrait justificatif et article cité dans les deux langues | 10 |
| Limitations chiffrée | Faite | 11 |

## 2. Données Gold

- **Dev Silver** : 54 questions (26 dans le périmètre : 20 FR, 6 tunisien ; 28 hors périmètre), déjà utilisées pour concevoir les prompts.
- **Jeu Gold** (`data/raw/arabic/questions_gold_premiere_revue.csv`) : 50 questions — 15 tunisien, 10 arabizi, 15 arabe standard, 10 hors périmètre. **Questions proposées par une IA, validées et étiquetées par un seul annotateur humain**, plusieurs articles acceptés par question ; 3 étiquettes corrigées après lecture du texte (article 122). Catégories finales : 37 avec article, 2 sans article (pas de majoration de nuit dans le Code), 11 hors périmètre.
- Paramètres identiques à Silver, **aucun réglage sur le jeu Gold** : BM25 (k1 1,5 ; b 0,75 ; seuil 9,085), e5-base, fusion RRF (k 60), RAG P2V avec qwen2.5:3b (température 0, graine 2026).

## 3. Transfert vers le tunisien, l'arabizi et l'arabe

Recherche, article accepté dans le top 5 (R@5) :

| Langue | BM25 | e5 | Hybride |
|---|---|---|---|
| Arabe standard (15) | 11 | 11 | **13** |
| Tunisien (13) | 5 | 2 | **6** |
| Arabizi (9) | **3** | 0 | 1 |

RAG P2V :

| Langue | Bon article cité | Refus à tort | Abstention correcte |
|---|---|---|---|
| Arabe standard | 7/15 | 2/15 | 3/4 |
| Tunisien | 2/13 | 10/13 | 5/6 |
| Arabizi | 0/9 | 6/9 | 3/3 |
| *Référence : français (dev)* | *16/20* | *3/20* | *21/22* |

Le seuil BM25 classique refuse à tort 11/13 questions tunisiennes et 9/9 en arabizi.

**Constat** : le transfert vers le dialecte échoue, et le goulot est la **recherche** — si l'article n'est pas retrouvé, le RAG ne peut que s'abstenir.

## 4. Audit des hallucinations et de l'abstention

Sur le dev (5 variantes de prompt, 54 questions) :

| Variante | Citations inventées | Bon article /26 | Hors périmètre refusé /28 | Refus à tort /26 |
|---|---|---|---|---|
| P0 — LLM seul | 37 | 0 | 0 | 0 |
| P1 — RAG libre | 0 | 20 | 0 | 0 |
| P2 — JSON + citation obligatoire + abstention | 0 | 18 | 26 | 2 |
| P3 — P2 + few-shot | 3 | 19 | 22 | 1 |
| P2V — P2 + vérification des citations | **0** | 18 | **26** | 3 |

Après correction des citations arabes (« الفصل 14 » était rejeté), une nouvelle exécution donne P2V : 18/26, 27/28, 4/26. L'écart d'une question avec l'exécution précédente vient de la variabilité d'Ollama, malgré la température 0.

## 5. Biais entre langues et invariance (INV)

- **3 sujets posés dans les 4 langues** (articles 79, 122, 140) : français 3/3, arabe 3/3, **tunisien 0/3, arabizi 0/3** (recherche et RAG). Même réponse dans les 4 langues : **0/3**.
- **7 sujets en arabe, tunisien et arabizi** : RAG correct 3 / 0 / 0.

**Constat** : biais net en défaveur du dialecte. Le PDF demande de traiter les réponses différentes selon la langue « comme un biais à corriger » : voir section 7.

## 6. Question de recherche 1 — la citation obligatoire réduit-elle les hallucinations sans augmenter les refus injustifiés ?

Réponse non fondée = réponse donnée alors que la question est hors périmètre, ou sans citer l'article de référence. Bootstrap apparié, 10 000 tirages.

| Variante | Réponses non fondées /54 | Refus injustifiés /26 |
|---|---|---|
| P0 | 54 | 0 |
| P1 (RAG libre) | 34 | 0 |
| P2 | 8 | 2 |
| P2V | **7** | 3 |

P2V par rapport à P1 : −27 réponses non fondées (IC 95 % du taux [−63 %, −37 %]) ; +3 refus injustifiés (IC [0 %, +23 %]).

**Réponse** : oui pour les hallucinations (effet significatif) ; les refus injustifiés augmentent légèrement, sans que ce soit significatif sur cet effectif.

## 7. Question de recherche 2 — traduire la question en arabe standard avant de chercher bat-il la recherche directe ?

Évaluation seule : l'application n'est pas modifiée. 31 questions tunisien + arabizi.

| | Direct | Traduit par qwen 3B | Traduit par Gemini 3.1 Flash-Lite |
|---|---|---|---|
| Tunisien — hybride R@5 | 6/13 | 8/13 | **10/13** |
| Arabizi — hybride R@5 | 1/9 | 2/9 | **6/9** |
| e5 R@5 (total) | 2/22 | 7/22 | **15/22** |
| RAG bon article (total) | 2/22 | 5/22 | **9/22** |
| Refus à tort | 16/22 | 11/22 | **9/22** |
| Abstention correcte | 8/9 | 7/9 | 7/9 |

Avec Gemini : 10 questions gagnées, 1 perdue. Le traducteur 3B produit des sorties non arabes (12/31) ou contenant des caractères chinois (4/31).

**Réponse** : oui, **à condition que le traducteur comprenne le dialecte**. Cela corrige une grande partie du biais de la section 5, au prix d'une dépendance à une API externe (seules les questions sont envoyées).

## 8. LLM-juge

- Juges testés sur les 23 réponses P2V non abstenues : qwen2.5:3b (local) et Gemini 3.5 Flash (API gratuite), température 0.
- Accord avec une **annotation de référence faite par une IA (Claude)** :

| Juge | Fidélité (κ) | Répond à la question (κ) |
|---|---|---|
| qwen2.5:3b | 0,04 | −0,05 |
| Gemini 3.5 Flash | 0,58 | 1,00 |

- **Limite** : la référence n'est pas humaine, donc le juge **n'est pas validé** au sens Gold. Validation humaine à faire sur la fiche `reports/gold/llm_juge/annotation_humaine.csv`.
- Constat utile : selon la référence IA, 18/23 réponses sont fidèles mais seulement 6/23 répondent vraiment à la question. Elles sont souvent réduites au seul numéro d'article.

## 9. Divergences AR / FR

- Détecteur par règles explicables : nombres, renvois vers d'autres articles, modalité (doit / peut / interdit), négations, longueur.
- 227 articles signalés sur 436. Le signal est bruité, à cause des artefacts d'extraction du PDF.
- Échantillon de 60 articles tiré au hasard (graine 2026), à annoter à l'aveugle, avec un guide. **Précision et rappel pas encore mesurés.**

## 10. Explications

Chaque réponse RAG affiche l'article cité dans les deux langues, avec un extrait justificatif. Une citation non fournie entraîne l'abstention (P2V). Le message d'abstention est rédigé dans l'écriture de la question.

## 11. Limitations (chiffrées)

1. **Jeux de développement** uniquement : 54 + 50 questions ; une question vaut environ 2 à 8 points selon le sous-groupe. Mesure unique sur `test_locked` non faite.
2. **Données Gold** proposées par une IA et étiquetées par **un seul annotateur** : aucun kappa inter-annotateurs.
3. **Transfert vers le dialecte** faible sans traduction : RAG correct tunisien 2/13, arabizi 0/9.
4. **Refus à tort** : 3 à 4 sur 26 en français (12–15 %) avec P2V.
5. **Variabilité** d'une exécution à l'autre : environ une question.
6. **Réponses trop courtes** : environ 17 sur 23 se limitent au numéro d'article (référence IA).
7. **LLM-juge non validé** contre un humain ; le juge local 3B est inutilisable (κ ≈ 0).
8. **Divergences AR / FR** : détecteur non évalué, signal bruité (227/436).
9. **Fine-tuning** (Silver) : l'alignement FR↔AR s'améliore, mais la recherche question → article se dégrade (R@5 22 → 9,33).
10. **Dépendance externe** si la traduction par Gemini était intégrée : quotas gratuits atteints pendant les essais, et les modèles en ligne changent de version.
11. **Information, pas conseil** : corpus limité au Code du travail.

## 12. Reste à faire avant la clôture Gold

- Annotation humaine : 23 réponses pour le juge, 60 articles pour les divergences.
- Décision (avec l'encadrant) sur l'intégration de « traduire puis chercher » dans l'application.
- Mesure unique sur `test_locked`.
- Diapos Gold.
