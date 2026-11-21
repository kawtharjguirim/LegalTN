# LegalTN — ce qui a été fait au Silver et au Gold, et comment continuer

Ce guide sert à reprendre le travail seule : pour chaque partie, **ce qui existe**, **la commande
qui le reproduit**, **le résultat obtenu**, puis **les améliorations à faire, étape par étape**.
Les chiffres détaillés sont dans les `RESULTATS.md` cités ; l'historique complet dans
`experiments.md`.

> Mot clé du guide : **« à relire »**. Beaucoup de références (gold NER, jugements, questions)
> ont été produites par Claude, pas par un humain. Les relire est l'amélioration qui rend
> les chiffres solides ; elle ne demande aucun code.

---

## 0. Avant toute commande

Dans PowerShell, depuis `D:\LegalTN\LegalTN-silver` :

```powershell
. .\env_silver.ps1
```

Cela place Python, les caches et les modèles sur `D:\LegalTN-cache` et définit `$Py`. Ensuite
toutes les commandes s'écrivent `& $Py -X utf8 -m <module> ...`.

- **Ollama** doit tourner pour tout ce qui appelle un LLM (`ollama list` doit montrer
  `qwen2.5:3b` et `qwen2.5:7b`).
- **Carte graphique de 4 Go** : ne pas laisser un serveur de démo ouvert pendant une mesure ;
  e5 peut tourner sur processeur (`--appareil cpu`) pour laisser la carte au LLM.
- **Disque C** : libérer au moins 10 Go. Quand C est plein, Windows ne peut plus agrandir le
  fichier d'échange : plantages (« fichier de pagination insuffisant », erreurs CUDA).
- **Tests** : `& $Py -m pytest -q` (attendu : tout réussi, 1 xfail connu sur le CDI).
- **Ne jamais mesurer sur `data/test_locked/`** avant la toute fin : tous les réglages se font
  sur `data/dev/`.

Après chaque expérience : ajouter une entrée datée dans `experiments.md` (ce qui a changé,
chiffres, limites), puis commit.

---

## 1. Palier Silver (branche `kawthar-silver`)

### 1.1 Alignement AR/FR par embeddings

| | |
|---|---|
| Code | `src/alignement_embeddings/` (`aligner.py`, `evaluer.py`) |
| Commande | `& $Py -X utf8 -m src.alignement_embeddings.evaluer --sortie reports/silver/alignement` |
| Résultat | LaBSE et e5 seuls : 0,975 ; hybride (embeddings + numéro d'article, λ = 0,1) : 1,000 sur le gold de 160 paires |
| Rapport | `reports/silver/alignement/RESULTATS.md` |

**Limite** : le gold de 160 paires vient des sorties de numérotation du Bronze (biais
favorable à la méthode hybride).

**Améliorer** :
1. Annoter à la main `data/dev/alignement_dev_v2_a_annoter.csv` et
   `data/dev/rappel_alignement_a_annoter_v1.csv` en privilégiant les articles **où le numéro ne
   suffit pas** (articles bis, articles abrogés, plages « 391 à 396 »).
2. Relancer `evaluer` : si l'hybride baisse sous 1,000, c'est la mesure honnête.

### 1.2 NER juridique (ROLE, INSTITUTION, DELAI, MONTANT)

| | |
|---|---|
| Code | `src/ner_juridique/` : `regles.py`, `pre_annoter.py`, `entrainer.py`, `evaluer_gold.py`, `predire.py` |
| Données | lots dev `data/a_annoter/ner_dev_fr_v1.csv` et `ner_dev_ar_v1.csv` (60 phrases chacun) |
| Entraîner | `& $Py -X utf8 -m src.ner_juridique.entrainer --langue fr --modeles crf camembert xlmr` (3 graines) |
| Évaluer | `& $Py -X utf8 -m src.ner_juridique.evaluer_gold --langue fr --accepter-claude` (puis `ar`) |
| Résultat (pré-gold Claude, F1 strict / souple) | FR : règles 0,423 / 0,620 ; XLM-R 0,479 / 0,644. AR : règles 0,484 / 0,603 ; AraBERT 0,416 / 0,568 |
| Rapport | `reports/silver/ner/RESULTATS.md` (+ erreurs par phrase dans `erreurs_pregold_dev_*.csv`) |

**Limite principale** : le gold des 120 phrases est un **pré-gold de Claude** (statut
`verifie_claude`). `--accepter-claude` est obligatoire tant qu'il n'est pas relu.

**Améliorer** (dans cet ordre) :
1. **Relire le pré-gold** : ouvrir `outils/annotateur_ner.html` dans Chrome, *Ouvrir un lot
   CSV…*, vérifier chaque phrase, corriger, `Entrée` (la phrase passe en `verifie`), puis
   *Enregistrer le CSV* **sur le fichier d'origine**. Conventions à vérifier :
   `data/a_annoter/LISEZMOI.md`.
2. Relancer `evaluer_gold` **sans** `--accepter-claude` : ce sont alors des chiffres sur un
   gold humain.
3. Le rappel est faible et hérité des règles (le modèle apprend sur les sorties des règles).
   Pour progresser : lire `erreurs_pregold_dev_fr.csv`, ajouter les motifs oubliés dans
   `regles.py` (ex. délais « dans la quinzaine », institutions arabes), relancer
   `pre_annoter.py` puis `entrainer`.
4. Annoter les lots test (`ner_test_*_v1.csv`) puis les geler dans `data/test_locked/` avec
   leur empreinte SHA-256 ; ne les évaluer qu'une fois, à la fin.

### 1.3 Recherche (RAG) dense et hybride, bilingue

| | |
|---|---|
| Code | `src/rag/recherche.py` (BM25, e5, fusion RRF k = 60), `src/rag/evaluer.py` |
| Commande | `& $Py -X utf8 -m src.rag.evaluer --sortie reports/silver/rag` |
| Résultat | hybride BM25 + e5 : R@1 FR 1,00, AR 0,62 (BM25 seul : 0,95 / 0,52) ; 18 configurations d'ablation dans `ablations_rag.csv` |
| Rapport | `reports/silver/rag/RESULTATS.md` |

**Limites** : 21 questions arabes traduites par Claude (`data/dev/questions_dev_ar_traduites_v1.csv`,
statut `a_valider`) ; dev déjà consulté pour régler les seuils.

**Améliorer** :
1. Relire les 21 traductions arabes (colonne `statut` → `verifie`, corriger `question`).
2. L'arabe est le point faible (0,62). Pistes, à tester une par une sur le dev :
   - corriger d'abord le corpus arabe (voir 2.2 : chiffres faux) ;
   - essayer un encodeur arabe ou plus grand (`multilingual-e5-large` si la mémoire le permet) ;
   - chercher dans les deux langues et fusionner (question AR → articles FR alignés).
3. Ajouter des questions dev **nouvelles** (jamais vues) pour avoir une mesure non optimiste.

### 1.4 LLM : réponse rédigée et résumé en langage clair

| | |
|---|---|
| Code | `src/rag/generer.py` (prompts : zero-shot, few-shot, citation forcée), `src/rag/evaluer_llm.py` |
| Commande | `& $Py -X utf8 -m src.rag.evaluer_llm --sortie reports/silver/llm` |
| Résultat (qwen2.5:3b) | citation forcée : référence citée 0,667, citation inventée 0,000 ; hors périmètre refusé 1,00 avec le seuil |
| Rapport | `reports/silver/llm/RESULTATS.md` |

**Limite** : le LLM n'est pas déterministe malgré la température 0 ; 40 résumés jamais notés.

**Améliorer** :
1. **Noter les 40 résumés** : `reports/silver/llm/resumes_a_noter.csv`, colonnes
   `exactitude_1_5` et `clarte_1_5`. C'est la seule mesure de qualité des résumés.
2. Mesurer le bruit : relancer 3 fois et rapporter moyenne ± écart.

### 1.5 Démo, capsule, slides

- Démo : `DEMO_SILVER.md` (scénario), `.\demo_silver.ps1` (vérifications + lancement),
  moteur `src/rag/service.py` (`api.py --moteur hybride`).
- Capsule : `reports/silver/capsule/` (MP4 + SRT), générée par
  `src/rapports/generer_capsule_silver.py`.

---

## 2. Palier Gold (branche `kawthar-gold`)

### 2.1 Audit : hallucinations, abstention, robustesse, écart de langues

| | |
|---|---|
| Code | `src/audit/perturbations.py` (sans accents, faute de frappe, politesse, alif…), `src/audit/audit.py`, `src/audit/calibrer_signal.py` |
| Commande | `& $Py -X utf8 -m src.audit.audit --sortie reports/gold/audit` (~493 requêtes, long) |
| Résultat | 0 article inventé, 0 question hors périmètre répondue ; sans accents : décision identique 0,500 → **0,944** après correctif ; paraphrase 0,571 ; même réponse juste FR et AR : 12/21 |
| Correctif livré | signal d'abstention normalisé (`service.abstenir`) : FR normalisé < 0,8567 ; AR brut < 0,8217 **ou** normalisé < 0,8188 |
| Rapport | `reports/gold/audit/RESULTATS.md` (versions avant correctif conservées dans les sous-dossiers) |

**À relire** : 42 paraphrases de Claude, `data/dev/questions_paraphrases_v1.csv` (statut
`a_valider`).

**Améliorer** :
1. **Paraphrases (0,643)** : c'est le point de robustesse le plus faible. Lire dans
   `audit_details.csv` les paraphrases qui changent d'article ; pistes : réécriture de la
   question par le LLM avant la recherche, ou ajouter les intitulés de section aux articles
   indexés.
2. **Écart FR/AR (11/21)** : dépend surtout de 1.3 et 2.2.
3. Les seuils ont été réglés sur un dev déjà consulté, avec seulement 3 questions arabes hors
   périmètre : ajouter une dizaine de questions arabes hors périmètre et relancer
   `calibrer_signal`.

### 2.2 Divergences AR/FR

| | |
|---|---|
| Code | `src/divergences/nombres.py` (nombres en chiffres et en lettres FR/AR), `detecter.py`, `evaluer.py` |
| Commandes | `& $Py -X utf8 -m src.divergences.detecter` puis `& $Py -X utf8 -m src.divergences.evaluer --jugements data/a_annoter/divergences_jugements_claude_v1.json` |
| Résultat | paires à problème : 92 % (similarité faible), 75 % (nombres différents), 0 % (hasard) ; **aucune divergence juridique réelle** ; 8 défauts d'OCR changent une règle en arabe |
| Rapport | `reports/gold/divergences/RESULTATS.md` ; classement complet `paires_scores.csv` |

**À relire** : 34 jugements de Claude dans `data/a_annoter/divergences_echantillon_v1.csv`
(mettre `statut` = `verifie` : `evaluer` ne réécrit jamais une ligne humaine).

**Améliorer** (impact direct sur la démo) :
1. **Corriger le corpus arabe** des 8 articles signalés `impact_juridique = true`, en vérifiant
   sur l'image du PDF : art. 64 (congé de maternité : 30 et 15 jours), art. 90 (taux 75 %,
   25 %, 50 %), art. 425 (288 dinars), art. 351 (délai de 3 mois), art. 234, 94-14, et les
   renvois « 2779 », « 2854 » (279, 284). Puis relancer `detecter` et la recherche.
2. Vérifier AR-335 : le contenu français de l'article 335 manque dans le corpus.
3. Juger d'autres paires parmi les 123 à écart de nombres, en priorité les articles cités par
   la démo.
4. Bug connu du convertisseur : « ستة عشر وثمانية عشر » est lu 34 (deux nombres additionnés).

### 2.3 Questions en tunisien (derja, arabizi)

| | |
|---|---|
| Code | `src/tunisien/arabizi.py` (détection, translittération), `traduction.py` (cache `runs/cache_traductions.json`), `evaluer.py` |
| Commande | `& $Py -X utf8 -m src.tunisien.evaluer --sortie reports/gold/tunisien --modele-traduction qwen2.5:7b` |
| Résultat (R@1 / R@5) | multilingue direct 0,000 / 0,033 ; traduction FR par 3B 0,100 / 0,400 ; **traduction FR par 7B 0,267 / 0,500** ; détection arabizi 100 % |
| Rapport | `reports/gold/tunisien/RESULTATS.md` (+ `qwen7b/`) |

**À relire** : 24 questions écrites par Claude dans `data/dev/questions_tun_v1.csv`. Tu parles
la derja : c'est l'endroit où ton jugement vaut le plus (formulations naturelles ou non ?).

**Améliorer** :
1. Écrire 20 à 30 questions **à toi**, comme les poserait un vrai salarié ; c'est le meilleur
   test.
2. Améliorer la traduction : ajouter au prompt un petit lexique derja → français
   (« khedma » travail, « chhar » mois, « conji » congé, « patron » employeur…) et 3 exemples.
3. Brancher la traduction dans la démo quand la question est détectée comme tunisienne
   (`est_tunisien` puis `traduire`, avant la recherche).
4. Mieux refuser le hors périmètre (7/9 avec le 7B) : appliquer le seuil d'abstention à la
   question **traduite**.

### 2.4 LLM-juge de fidélité

| | |
|---|---|
| Code | `src/juge/juge.py` (`echantillon`, `appliquer`, `juger`) ; tests `tests/test_juge.py` |
| Commandes | `& $Py -X utf8 -m src.juge.juge juger --modele qwen2.5:7b` (≈ 8 min), puis `--modele qwen2.5:3b` |
| Résultat (contre la référence de Claude) | 7B : κ 0,448 ; 13/13 réponses infidèles signalées ; 6 fausses alertes sur 32 ; 3B : κ 0,150 |
| Rapport | `reports/gold/juge/RESULTATS.md` (consigne v1 conservée dans `v1_consigne_verdict/`) |

**À faire pour que le juge soit « validé »** :
1. Ouvrir `outils/juge_fidelite.html` dans Chrome ou Edge (double-clic), *Ouvrir l'échantillon
   CSV…* → `data/a_annoter/juge_echantillon_v1.csv`. Pour chaque réponse : lire question,
   réponse et articles cités, puis `1` fidèle, `2` partiel, `3` infidèle. Le verdict de Claude
   reste caché jusqu'à ton choix (jugement à l'aveugle). *Enregistrer le CSV* (`Ctrl+S`) sur le
   fichier d'origine.
2. `& $Py -X utf8 -m src.juge.juge accord` : écrit `reports/gold/juge/accord_humain.json` avec
   l'accord toi / Claude, toi / qwen2.5:7b et toi / qwen2.5:3b (sans relancer les LLM). Ce sont
   ces chiffres qui « valident » le juge.
3. Améliorer le juge : il confond « partiel » et « fidèle ». Pistes : 2 exemples par verdict
   dans la consigne, ou demander d'abord la liste des affirmations de la réponse puis de les
   vérifier une à une.

---

## 3. Liste d'actions dans l'ordre conseillé

Cocher au fur et à mesure.

**Validations humaines (aucun code)**
- [ ] `verdict_humain` des 56 réponses du juge (2.4)
- [ ] 120 phrases du pré-gold NER dans l'outil d'annotation (1.2)
- [ ] 34 jugements de divergences, surtout les 8 à impact juridique (2.2)
- [ ] 24 questions tunisiennes + 42 paraphrases + 21 traductions arabes (2.3, 2.1, 1.3)
- [ ] notes des 40 résumés (1.4)

**Améliorations techniques**
- [ ] corriger les chiffres faux du corpus arabe (2.2) → relancer RAG et audit
- [ ] traduction tunisienne dans la démo, avec lexique derja (2.3)
- [ ] robustesse aux paraphrases (2.1)
- [ ] relancer les évaluations sur gold humain, sans `--accepter-claude` (1.2)

**Fin de projet**
- [ ] geler les lots test NER dans `data/test_locked/` et évaluer une seule fois
- [ ] mettre à jour slides, démo et capsule avec les chiffres Gold
- [ ] commit + push, entrée `experiments.md` à chaque étape

---

## 4. Où sont les fichiers à relire

| Fichier | Quoi | Colonne à remplir |
|---|---|---|
| `data/a_annoter/ner_dev_fr_v1.csv`, `ner_dev_ar_v1.csv` | pré-gold NER | via `outils/annotateur_ner.html` |
| `data/a_annoter/juge_echantillon_v1.csv` | fidélité des réponses | `verdict_humain` |
| `data/a_annoter/divergences_echantillon_v1.csv` | divergences AR/FR | `verdict`, `statut` → `verifie` |
| `data/dev/questions_tun_v1.csv` | questions tunisiennes | `statut`, `commentaire` |
| `data/dev/questions_paraphrases_v1.csv` | paraphrases | `statut`, `paraphrase` |
| `data/dev/questions_dev_ar_traduites_v1.csv` | traductions arabes | `statut`, `question` |
| `reports/silver/llm/resumes_a_noter.csv` | résumés | `exactitude_1_5`, `clarte_1_5` |

---

## 5. Palier Platinum (branche `kawthar-platinum`)

Rapport brouillon : `reports/platinum/RAPPORT.md` (tableau d'état en annexe). Ce qu'il reste à faire :

1. **Relire les obligations** : `outils/annotateur_obligations.html` → ouvrir `data/a_annoter/obligations_dev_claude_v1.csv`, relire (touches `1`–`4`, `Entrée`), enregistrer sur le même fichier ; puis `python -X utf8 -m src.obligation_extraction.evaluer_obligations --gold data/a_annoter/obligations_dev_claude_v1.csv --predictions data/dev/obligations_predictions_dev_v1.csv`.
2. **Mesurer le test une seule fois**, après relecture de `obligations_test_claude_v1.csv` : lancer l'extracteur sur `data/test_locked/obligations_candidats_test_v1.csv`, évaluer, consigner dans `experiments.md`. Ne plus toucher aux règles ensuite.
3. **Licence** : renseigner `data/publication/legaltn_v1/LICENCE.md`, puis publier (toi). Test des obligations : `preparer --avec-test` seulement après l'étape 2.
4. **Étude d'utilité** : `etude_utilite/PROTOCOLE.md` (faire valider les 12 tâches par un juriste, pilote à 2 personnes, 12 à 20 étudiants). Passation avec `outils/etude_utilite.html`, résultats dans `etude_utilite/resultats/`, notation des colonnes `note_reponse` / `note_article`, puis `python -X utf8 -m src.etude.analyser`.
5. **Corriger les 8 articles arabes** (voir 2.2) avant de publier le texte arabe.
