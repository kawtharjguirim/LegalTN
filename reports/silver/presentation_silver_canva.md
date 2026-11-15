# LegalTN — Brief pour créer la présentation de la validation Silver

> **Instructions pour Claude / Canva (à lire avant de créer les diapositives)**
> - Crée une présentation de **16 diapositives** en français, format 16:9.
> - Style : moderne, sobre, institutionnel. Couleurs : indigo `#4F46E5` (principale), bleu nuit `#0F172A`
>   (fonds sombres, titres), gris clair `#F4F6FB` (fonds), rouge `#E11D48` uniquement pour une alerte
>   ou une limite, vert `#059669` pour un résultat positif. Police sans empattement (Inter, Segoe UI).
> - **N'invente aucun chiffre.** Utilise uniquement les chiffres de ce document, tels quels
>   (format « 21/27 », pas de pourcentage ajouté). Si une case dit **[À COMPLÉTER]** ou **[EN COURS]**,
>   laisse-la visible telle quelle : l'équipe la remplira.
> - Garde chaque diapositive légère : un titre, 3 à 5 points courts ou un tableau, un visuel.
>   Les détails vont dans les **notes de l'orateur**.
> - Les tableaux doivent rester lisibles : 6 colonnes maximum, chiffres alignés à droite.

---

## Contexte à connaître (ne pas mettre tel quel sur une diapositive)

- **Projet** : LegalTN, assistant d'information sur le **Code du travail tunisien**, bilingue arabe /
  français, avec questions en français, arabe, tunisien et arabizi. Il retrouve l'article pertinent, le
  cite avec sa page, et **s'abstient** quand la question sort du Code.
- **Séance** : validation du **palier Silver** (module NLP et spécialisation, ESPRIM 2026-2027).
- **Ce que demande le mail de l'enseignante** (5 points, à couvrir explicitement) :
  1. mise en œuvre des **modèles appris** (encodeurs, fine-tuning) ;
  2. intégration des **LLM** et des **techniques de prompting** ;
  3. mise en place du **RAG** et de la **recherche sémantique** ;
  4. **résultats expérimentaux**, comparaisons avec les **baselines**, **études d'ablation** ;
  5. **démonstration fonctionnelle**.
- **Règle d'évaluation suivie** : tous les chiffres sont mesurés sur le **jeu de développement**
  (dev v2 : 56 questions, 27 dans le périmètre — 21 en français, 6 en tunisien écrit en arabizi —
  et 29 hors périmètre). Le **jeu de test gelé** (40 questions) n'a jamais été utilisé pour régler
  quoi que ce soit ; il sera mesuré **une seule fois**, à la fin.
- Tout est exécuté **en local**, avec des modèles **ouverts** (exigence du cahier des charges).

---

## Diapositive 1 — Titre

- **Titre** : LegalTN — Validation Silver
- **Sous-titre** : Assistant juridique bilingue sur le Code du travail tunisien : recherche sémantique, RAG et LLM local
- **Bas de page** : Module NLP et spécialisation · ESPRIM 2026-2027 · Équipe : [À COMPLÉTER] · Date : [À COMPLÉTER]
- **Visuel** : logo LegalTN, fond bleu nuit avec un dégradé indigo discret.
- **Notes** : se présenter, rappeler en une phrase le but du projet.

## Diapositive 2 — Le problème

- **Titre** : Retrouver la bonne règle, dans la bonne langue, sans inventer
- **Points** :
  - L'utilisateur connaît son problème, pas le numéro d'article.
  - Il pose sa question en français, en arabe, en tunisien ou en arabizi.
  - Une réponse juridique inventée est dangereuse : il faut **citer** ou **s'abstenir**.
- **Visuel** : trois bulles de question (FR / AR / arabizi) qui pointent vers un article cité.
- **Notes** : reprendre la problématique du cahier des charges : traçabilité et limitation des hallucinations.

## Diapositive 3 — Où nous en étions au Bronze

- **Titre** : Point de départ (Bronze)
- **Points** :
  - Corpus : Code du travail bilingue, **496 articles FR** et **491 articles AR** indexés.
  - Alignement AR ↔ FR par numéro d'article : **494 paires** ; **100 paires du dev vérifiées à la main, 0 erreur**.
  - Recherche lexicale **BM25** + règle d'abstention (seuil 9,085).
  - Démo web et API locales.
- **Visuel** : schéma simple « Question → BM25 → Article cité / Abstention ».
- **Notes** : Silver ajoute les modèles appris, le LLM et le RAG par-dessus cette base, sans la jeter : BM25 reste la **baseline**.

## Diapositive 4 — Architecture Silver

- **Titre** : La chaîne complète
- **Visuel principal (schéma de gauche à droite)** :
  Question → **Pipeline de traitement** (langue, arabizi, mots vides, normalisation, sigles, SymSpell, synonymes)
  → **Recherche** (BM25 · dense e5 · hybride) → **Top 3 articles FR + AR** → **LLM local (RAG)**
  → **Vérification des citations** → Réponse citée **ou** abstention
- **Notes** : chaque bloc a été mesuré séparément (diapositives suivantes). Tout tourne en local, sans API payante.

## Diapositive 5 — Pipeline de traitement des questions

- **Titre** : Comprendre la question avant de chercher
- **Points** (8 étapes) : détection de langue (fr / ar / tunisien / arabizi) → translittération arabizi →
  mots vides (négations et modaux protégés) → normalisation → lexique tunisien et sigles (CDI, CDD, SMIG, SMAG, CNSS)
  → racinisation arabe légère → correction orthographique **SymSpell** → synonymes.
- **Encadré « exemple réel »** : « quel est le préavi pour un contart CDI ? » → « Vouliez-vous dire : quel est le préavis pour un contrat à durée indéterminée ? »
- **Mini-tableau (dev v2, questions avec fautes de frappe générées, graine 2026)** :

| Questions avec fautes | R@1 | R@5 |
|---|---:|---:|
| sans correction | 19/27 | 20/27 |
| avec correction SymSpell | 21/27 | 21/27 |

- **Notes** : SymSpell rattrape le niveau des questions propres (21/27). Coût : plus de questions hors périmètre acceptées (29/29 → 25/29 refusées).

## Diapositive 6 — Modèles appris (1) : encodeur et recherche sémantique

- **Titre** : Recherche sémantique avec un encodeur multilingue
- **Points** :
  - Encodeur pré-entraîné **intfloat/multilingual-e5-base** (arabe + français).
  - Chaque article (FR et AR) devient un vecteur ; la question aussi ; on compare par similarité cosinus.
  - **Recherche croisée** : une question est comparée aux deux langues à la fois.
  - **Hybride** : fusion BM25 + dense par *Reciprocal Rank Fusion* (k = 60, valeur standard, non réglée).
- **Visuel** : deux nuages de points (FR / AR) avec une question au milieu reliée aux articles proches.
- **Notes** : « Recherche sémantique » = retrouver le sens, pas seulement les mêmes mots.

## Diapositive 7 — Modèles appris (2) : fine-tuning de l'encodeur

- **Titre** : Fine-tuning de l'encodeur sur les paires FR ↔ AR
- **Points** :
  - Données réelles : **436 paires** d'articles présents dans les deux langues.
  - Découpage par article (graine fixe) : **349 entraînement / 87 évaluation**, aucun article des deux côtés.
  - Apprentissage contrastif (*MultipleNegativesRankingLoss*), 2 époques, 3 graines (13, 42, 2026).
  - Réglages fixés **avant** toute mesure.
- Entraîné sur GPU (GTX 1650) ; couche de vocabulaire gelée pour tenir en mémoire.
- **Tableau** :

| Mesure | Avant fine-tuning | Après (moyenne, 3 graines) |
|---|---:|---:|
| Arabe → bon article français, R@1 (/87) | 84 | **87** |
| Français → bon article arabe, R@1 (/87) | 80 | **86,67** |
| Questions du dev, R@1 (/27) | 20 | **5,67** |
| Questions du dev, R@5 (/27) | 22 | **9,33** |

- **Message clé** : le fine-tuning **réussit sa tâche** (alignement parfait) mais **dégrade la recherche à partir de questions**. Nous gardons donc l'encodeur pré-entraîné.
- **Notes** : résultat négatif stable sur 3 graines. Le modèle a appris à relier deux longs articles, pas une question courte à un article. Leçon : il faut entraîner sur la tâche finale (question → article). C'est aussi notre seule mesure **côté arabe** pour l'instant (via l'alignement).

## Diapositive 8 — LLM et techniques de prompting

- **Titre** : Un LLM ouvert, en local, encadré par le prompt
- **Points** :
  - Modèle : **Qwen2.5 3B Instruct** (via Ollama), sur le PC de l'équipe, température 0, graine fixe.
  - 4 techniques de prompting comparées :
    - **P0** : LLM seul, sans article fourni (baseline négative) ;
    - **P1** : RAG, consignes en zéro-shot, réponse libre ;
    - **P2** : RAG + sortie **JSON imposée** + règle d'abstention explicite ;
    - **P3** : P2 + **2 exemples (few-shot)**, exclus de l'évaluation.
- **Encadré** : extrait du prompt système — « Réponds UNIQUEMENT à partir des articles fournis. N'invente jamais de numéro d'article. Si les articles ne permettent pas de répondre, mets "abstention": true. »
- **Notes** : le prompt impose les contraintes du cahier des charges (ne pas inventer, citer, s'abstenir).

## Diapositive 9 — RAG et garde-fou anti-hallucination

- **Titre** : RAG : le LLM répond « à livre ouvert »
- **Visuel (schéma)** : Question → 3 articles retrouvés (texte FR + AR) → LLM → **Vérification** : chaque article cité fait-il partie des articles fournis ? → oui : réponse affichée / non : **abstention**
- **Points** :
  - Variante **P2V** = P2 + vérification automatique des citations.
  - Une réponse sans citation, ou citant un article non fourni, est **rejetée**.
  - Si le LLM est éteint, l'application se rabat sur la recherche classique.
- **Notes** : c'est la protection la plus simple et la plus démontrable contre les articles inventés.

## Diapositive 10 — Résultats : baselines et recherche

- **Titre** : Recherche : comparaison aux baselines (dev v2)
- **Tableau 1 — baselines triviales et BM25** :

| Système | R@1 | R@5 | Refus hors périmètre |
|---|---:|---:|---:|
| Aléatoire (graine 2026) | 0/27 | 0/27 | 0/29 |
| Mots communs | 13/27 | 23/27 | 0/29 |
| BM25 + seuil 9,085 | 21/27 | 21/27 | 27/29 |
| Pipeline complet + seuil | 20/27 | 22/27 | 23/29 |

- **Tableau 2 — recherche par langue, sans seuil (R@1 / R@5)** :

| Langue (n) | BM25 | Dense e5 | Hybride RRF |
|---|---:|---:|---:|
| Français (21) | 20 / 21 | **21 / 21** | 21 / 21 |
| Tunisien arabizi (6) | **1 / 3** | 0 / 1 | 0 / 0 |
| Arabe | non mesurable (0 question) | — | — |

- **Notes** : le dense corrige la seule erreur de BM25 en français, mais échoue sur l'arabizi (caractères latins + chiffres). Au total, l'hybride ne bat pas BM25 sur ce dev : on le dit, on ne le cache pas.

## Diapositive 11 — Résultats : génération (RAG)

- **Titre** : Le RAG supprime les articles inventés
- **Tableau (dev v2 sans les 2 exemples few-shot : 26 dans / 28 hors périmètre)** :

| Variante | Bon article cité (/26) | Fausses abstentions | Hors périmètre refusé (/28) | Citations non fournies |
|---|---:|---:|---:|---:|
| P0 LLM seul | 0 | 0 | 0 | 37 |
| P1 RAG libre | **20** | 0 | 0 | 0 |
| P2 RAG + JSON | 18 | 2 | **26** | 0 |
| P3 few-shot | 19 | 1 | 22 | 3 |
| P2V vérifié | 18 | 3 | **26** | **0** |

- **Message clé (en grand)** : sans articles, le LLM cite **0 bon article sur 26** ; avec le RAG, **18 à 20**.
- **Notes** : P1 cite le mieux mais ne refuse jamais rien ; P2/P2V offrent le meilleur compromis ; le few-shot n'aide pas l'abstention. Version retenue pour la démo : **P2V**.

## Diapositive 12 — Études d'ablation

- **Titre** : Quelle pièce apporte quoi ? (dev v2)
- **Tableau** :

| Pièce retirée ou ajoutée | Effet mesuré |
|---|---|
| Sans seuil d'abstention (BM25) | Hors périmètre refusés : 27/29 → **0/29** ; R@5 : 21/27 → 23/27 |
| + SymSpell (questions avec fautes) | R@1 : 18/27 → **21/27** ; refus hors périmètre : 29/29 → 25/29 |
| + translittération arabizi | Abstentions à tort tunisiennes : 4/6 → **0/6** ; mais refus hors périmètre tunisiens : 2/3 → 0/3 |
| Passages retirés au LLM (P0 vs P1) | Bon article cité : 20/26 → **0/26** |
| Sans format JSON + règle d'abstention (P1 vs P2) | Hors périmètre refusés : 26/28 → **0/28** |
| Sans vérification des citations (P2 vs P2V) | Réponses sans citation : 1 → **0** ; une fausse abstention de plus |

- **Notes** : chaque ligne vient d'une entrée datée de `experiments.md`.

## Diapositive 13 — Analyse d'erreurs et limites

- **Titre** : Ce qui ne marche pas encore (et pourquoi)
- **Points** :
  - **Arabe** : aucune question arabe dans le périmètre du dev → rappel arabe non mesurable sur des questions (seulement via l'alignement, diapo 7). Questions arabes à écrire par l'équipe.
  - **Arabizi** : 6 questions seulement ; l'encodeur e5 les comprend mal.
  - **Petits effectifs** : 27 questions → 1 question = 3,7 points ; pas de conclusion statistique.
  - **LLM 3B** : la phrase rédigée est souvent très courte ; temps de réponse observé en démo : environ **16 à 32 secondes** par question (contre environ 13 ms pour la recherche seule).
  - **Fidélité** des réponses rédigées : pas encore jugée par une grille humaine.
  - Exemples d'erreurs : « durée légale du travail hebdomadaire » ne trouve pas l'article 79 (« 48 heures par semaine ») ; « loyor » corrigé à tort en « loger ».
- **Notes** : montrer ces limites est une force, pas une faiblesse.

## Diapositive 14 — Démonstration

- **Titre** : Démonstration en direct
- **Déroulé à l'écran (liste numérotée)** :
  1. Mode classique : « Quel est le préavis de rupture d'un CDI ? » → correction du sigle, **article 14 bis, page 279**, surligné, version arabe disponible.
  2. Mode **Réponse rédigée (RAG)** : même question → réponse + extrait cité + articles FR et AR.
  3. Question hors périmètre : « Quelle est la capitale de la Tunisie ? » → **abstention**.
  4. Question en arabe (préparée par l'équipe) : [À COMPLÉTER].
  5. Mode debug : la question après chaque étape du pipeline.
- **Visuel** : capture de l'interface (barre latérale sombre, carte de résultat avec surlignage).
- **Notes** : prévenir que le mode RAG prend environ 30 secondes ; une vidéo de secours est prête : [À COMPLÉTER].

## Diapositive 15 — Qualité et reproductibilité

- **Titre** : Des résultats vérifiables
- **Points** :
  - Chaque chiffre est daté et traçable dans `experiments.md`, avec sa commande.
  - Jeu de test gelé protégé par empreintes **SHA-256**, vérifiées par les tests automatiques.
  - **98 tests automatiques** réussis.
  - Modèles ouverts, exécution locale, graines fixées.
  - Code : https://github.com/kawtharjguirim/LegalTN
- **Notes** : la mesure finale sur le test gelé sera faite une seule fois, sur la configuration figée.

## Diapositive 16 — Suite vers Gold

- **Titre** : Prochaines étapes
- **Points** :
  - Questions arabes et tunisiennes annotées par l'équipe → résultats par langue complets.
  - Mesure unique sur le jeu de test gelé.
  - Grille humaine de fidélité des réponses RAG.
  - Gold : extraction des obligations (qui / modal / quoi / quand), références croisées, divergences AR/FR.
- **Fin** : « Merci — questions ? »

---

## Questions probables du jury (pour préparer l'oral, pas pour les diapositives)

| Question | Réponse appuyée sur nos chiffres |
|---|---|
| Comment évitez-vous les hallucinations ? | RAG + vérification des citations : 37 citations non justifiées sans passages (P0), 0 avec P2V. |
| Le RAG est-il meilleur que le LLM seul ? | Bon article cité : 0/26 sans passages, 18 à 20/26 avec. |
| La recherche sémantique bat-elle BM25 ? | En français oui (R@1 21/21 contre 20/21) ; en arabizi non ; au total non sur ce dev. |
| Avez-vous réglé quoi que ce soit sur le test ? | Non : test gelé, empreintes SHA-256 vérifiées par les tests, une seule mesure finale. |
| Et l'arabe ? | Mesuré via l'alignement FR ↔ AR (diapo 7) : 84/87 avant, 87/87 après fine-tuning ; questions arabes à écrire par l'équipe. |
| Le fine-tuning a-t-il servi ? | Il atteint 87/87 sur l'alignement mais fait chuter la recherche par questions (R@5 22 → 9,33/27) : nous ne l'utilisons pas, et c'est une leçon mesurée. |
| Pourquoi un modèle 3B ? | Ouvert, multilingue, tourne en local sur une carte graphique de 4 Go, sans coût ni envoi de données. |
