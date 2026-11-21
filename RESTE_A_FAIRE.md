# Ce qu'il te reste à faire (21 novembre 2026)

Tout ce qui pouvait être fait sans toi est fait. Ce qui suit **ne peut pas être fait à ta place** : il faut un
jugement humain, des participants ou une décision. Ordre conseillé = du plus rapide et utile au plus long.
Après chaque étape, relance la commande indiquée et note le résultat dans `experiments.md`.

Préparation (une fois par session de terminal) :
```powershell
cd D:\LegalTN\LegalTN-silver
. .\env_silver.ps1
```

## A. Relectures (à faire d'abord : elles rendent les chiffres « humains »)

| # | Quoi | Temps | Comment | Ensuite |
|---|---|---:|---|---|
| 1 | **56 verdicts du LLM-juge** | 40 min | Ouvrir `outils/juge_fidelite.html` (Chrome ou Edge), charger `data/a_annoter/juge_echantillon_v1.csv`, touches `1` fidèle, `2` partiel, `3` infidèle, `Ctrl+S` sur le même fichier | `& $Py -X utf8 -m src.juge.juge accord` |
| 2 | **120 phrases NER** (pré-gold de Claude) | 1 h 30 | `outils/annotateur_ner.html`, lots `data/a_annoter/ner_dev_fr_v1.csv` et `ner_dev_ar_v1.csv` ; `Entrée` valide une phrase ; enregistrer sur le fichier d'origine | `& $Py -X utf8 -m src.ner_juridique.evaluer_gold --langue fr` puis `--langue ar` (**sans** `--accepter-claude`) |
| 3 | **200 obligations du dev** | 2 h | `outils/annotateur_obligations.html`, fichier `data/a_annoter/obligations_dev_claude_v1.csv` ; touches `1`–`4` pour le type, corriger qui / quoi / quand, `Entrée` | `& $Py -X utf8 -m src.obligation_extraction.evaluer_obligations --gold data/a_annoter/obligations_dev_claude_v1.csv --predictions data/dev/obligations_predictions_dev_v1.csv --sortie reports/platinum/obligations/evaluation_dev_extracteur.json` |
| 4 | **100 obligations du test** | 1 h | Même outil, fichier `data/a_annoter/obligations_test_claude_v1.csv`. **Fixer tes conventions sur le dev avant**, puis ne plus toucher aux règles | voir « Mesure unique du test » ci-dessous |
| 5 | 34 paires de divergences | 30 min | Éditeur CSV : `data/a_annoter/divergences_echantillon_v1.csv`, colonnes `verdict` et `statut` (`verifie`) | `& $Py -X utf8 -m src.divergences.evaluer --jugements data/a_annoter/divergences_jugements_claude_v1.json` |
| 6 | 24 questions tunisiennes, 42 paraphrases, 21 traductions arabes | 1 h 15 | `data/dev/questions_tun_v1.csv`, `questions_paraphrases_v1.csv`, `questions_dev_ar_traduites_v1.csv` : colonne `statut` → `verifie`, corriger la question | relancer l'audit (`src.audit.audit`) si tu as changé des questions |
| 7 | 40 résumés (exactitude et clarté, 1 à 5) | 40 min | `reports/silver/llm/resumes_a_noter.csv`, colonnes `exactitude_1_5` et `clarte_1_5` | `& $Py -X utf8 -m src.rapports.tableau_de_bord` |
| 8 | **7 corrections du texte arabe à confirmer sur image** | 15 min | Ouvrir `data/processed/page_images/` aux pages 41 (art. 87), 48 (art. 100), 55 (art. 125), 73 (art. 176), 76 (art. 196), 82 (art. 227), 91 (art. 265) ; comparer avec `data/processed/corrections_ar.csv` (colonne `verification` = `francais`) ; corriger le fichier si l'image dit autre chose | `& $Py -X utf8 -m src.corpus.corriger_arabe` |
| 9 | Regroupement en 12 domaines | 30 min (avec un juriste) | `PLAGES` dans `src/domaine/etiquettes.py` | `& $Py -X utf8 -m src.domaine.evaluer` |

### Mesure unique du test des obligations (après l'étape 4)
```powershell
& $Py -X utf8 -m src.obligation_extraction.extraire_obligations --candidats data/test_locked/obligations_candidats_test_v1.csv --sortie reports/platinum/obligations/predictions_test.csv
& $Py -X utf8 -m src.obligation_extraction.evaluer_obligations --gold data/a_annoter/obligations_test_claude_v1.csv --predictions reports/platinum/obligations/predictions_test.csv --sortie reports/platinum/obligations/evaluation_test_extracteur.json
```
**Une seule fois.** Consigner le résultat dans `experiments.md`, ne plus modifier `extraire_obligations.py`.

## B. L'étude d'utilité (la plus longue : compter 2 à 3 semaines)

1. Faire valider les 12 tâches (`etude_utilite/taches_v1.csv`) par un enseignant ou un juriste.
2. Pilote avec 2 personnes (`outils/etude_utilite.html`), corriger les consignes.
3. Recruter 12 à 20 étudiants en droit ou administration (4 groupes G1 à G4, voir `etude_utilite/PROTOCOLE.md`). Démarrer l'application : `.\demarrer.ps1 -Port 8000 -Moteur hybride` (Ollama lancé pour la réponse rédigée).
4. Sauvegarder les exports dans `etude_utilite/resultats/`, remplir `note_reponse` et `note_article` (si possible par deux personnes sur 30 % des réponses).
5. `& $Py -X utf8 -m src.etude.analyser`, puis recopier `reports/platinum/etude_utilite/RESULTATS.md` dans la section 8 du rapport.

## C. Publication

1. Écrire à l'éditeur du Code (IORT) ou consulter les conditions de réutilisation ; noter la réponse dans `data/publication/legaltn_v1/LICENCE.md` et choisir la licence des annotations.
2. Régénérer : `& $Py -X utf8 -m src.publication.preparer` (variante complète `--avec-phrases --avec-test` **seulement** après la licence et la mesure du test).
3. Publier toi-même (GitHub, Zenodo, Hugging Face…), puis mettre le lien dans le rapport.

## D. Rendus finaux

1. **Rapport** : relire `reports/platinum/RAPPORT.md` (version étoffée), compléter la section 8 (étude), retirer les mentions « brouillon », exporter en PDF.
2. **Vidéo** : lancer `src/rapports/generer_capsule_silver.py` après avoir relu `DEMO_SILVER.md` ; ajouter le tableau de bord (`/tableau-de-bord`) au scénario.
3. Commit et push de `kawthar-platinum`, tag du palier.

## E. Ce qui reste volontairement ouvert (améliorations possibles)

- Ajouter 50 questions neuves (jusqu'à 200) et 40 paires d'alignement vérifiées (jusqu'à 200) : `data/dev/`.
- Obligations par analyse de dépendances (au lieu de règles) : nécessite un analyseur syntaxique (spaCy, Stanza) pour FR et AR.
- Corriger les articles arabes non traités : AR-344, AR-335, AR-24 (`reports/platinum/corpus_arabe/RESULTATS.md`).
