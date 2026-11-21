# Audit des hallucinations, de l'abstention et de la robustesse — palier Gold (20 novembre 2026)

Commande : `python -X utf8 -m src.audit.audit --sortie reports/gold/audit` (e5 sur processeur,
qwen2.5:3b sur la carte graphique). Détail par requête : `audit_details.csv` ; agrégats :
`audit_resultats.json`.

## Protocole

- Chaîne auditée = celle de la démo : recherche hybride BM25 + e5 (3 articles), seuil d'abstention
  par langue (fr 0,860 ; ar 0,822), puis qwen2.5:3b en **citation forcée**.
- Questions : dev v2 (21 FR et 6 tunisiennes dans le périmètre, 29 hors périmètre) + 21 traductions
  AR + 42 paraphrases FR/AR. **Traductions et paraphrases écrites par Claude, à valider.**
  Aucun jeu de test gelé n'est lu.
- **493 requêtes**, 310 réponses du LLM, **0 appel en échec**.
- **Attention : les sections 1 à 4 décrivent la première exécution (règle d'abstention du Silver).**
  Les chiffres de l'exécution finale (règle corrigée, 326 réponses du LLM) sont dans la section 5 et
  dans `audit_resultats.json` ; le tableau de bord lit ce dernier. Ex. paraphrase : décision
  identique 0,643 → **0,571** ; juste dans les deux langues : 11 → **12** sur 21.
- Chaque question originale est posée **3 fois** : l'écart entre ces répétitions donne le **bruit de
  référence** du LLM (non déterministe), à comparer aux effets des perturbations.

## 1. Hallucinations juridiques

| Mesure (310 réponses du LLM) | Taux |
|---|---:|
| Article **inventé** (inexistant dans le Code), avant filtre | **0,000** |
| Article cité hors des 3 extraits fournis, avant filtre | 0,013 (4 réponses) |
| Réponse sans citation `[Article N]`, avant filtre | 0,100 |
| Article inventé **affiché** à l'utilisateur | **0,000** |
| Question hors périmètre ayant reçu une réponse | **0,000** |

Les 4 citations hors contexte portent sur les articles 120 et 121, qui existent (questions sur la
rupture abusive) : ce sont des articles voisins, pas des inventions, et la citation forcée les a
bloquées. Aucun article inexistant n'a été produit.

## 2. Abstention par langue (questions originales)

| Langue | Fausse abstention (recherche) | Fausse abstention (finale) | Référence citée | Hors périmètre refusé |
|---|---:|---:|---:|---:|
| Français (21 / 23) | 0,000 | 0,143 | 0,810 | **1,000** |
| Arabe traduit (21) | 0,095 | 0,190 | 0,667 | – |
| Arabe hors périmètre (3) | – | – | – | **1,000** |
| **Tunisien (6 / 3)** | **1,000** | **1,000** | **0,000** | 1,000 |

Le système ne répond jamais hors périmètre, mais **refuse toutes les questions en tunisien**
(arabizi) : c'est le point 3 du palier Gold.

## 3. Robustesse INV — part des réponses identiques à l'original

| Perturbation | n | 1er article retrouvé | Décision (répondre / s'abstenir) | Articles cités |
|---|---:|---:|---:|---:|
| **Bruit de référence** (même question, 2 autres fois) | 154 | 1,000 | 0,974 | 0,974 |
| Minuscules (FR) | 21 | 1,000 | 0,952 | 0,952 |
| Sans ponctuation | 42 | 0,976 | 0,905 | 0,857 |
| Politesse ajoutée | 68 | 0,956 | 0,897 | 0,838 |
| Normalisation de l'alif (AR) | 11 | 1,000 | 0,909 | 0,727 |
| Faute de frappe | 60 | 0,767 | 0,833 | 0,767 |
| **Sans accents (FR)** | 18 | 0,556 | **0,500** | 0,444 |
| **Paraphrase** | 42 | **0,452** | 0,643 | 0,548 |

(Pour la ligne « sans accents », la colonne « 1er article » compte aussi les abstentions comme un
changement : le bon article reste en tête 17 fois sur 18.)

Lecture :
- Le LLM seul varie peu (bruit de référence : 2,6 % de décisions différentes) : les écarts plus
  grands viennent des perturbations.
- **Sans accents** : le bon article reste en tête 17 fois sur 18, mais le cosinus d'e5 baisse
  légèrement (ex. 0,884 → 0,858) et passe sous le seuil français 0,860 → **7 fausses abstentions
  sur 18**. Défaut du **seuil d'abstention**, pas de la recherche. Correctif à évaluer : seuil
  calculé sur la question normalisée, ou abstention seulement si BM25 (insensible aux accents) est
  lui aussi faible.
- **Paraphrase** : la recherche change d'article plus d'une fois sur deux. Elle reste dépendante
  du vocabulaire du texte de loi (« attributions », « ressort ») ; un utilisateur qui reformule
  avec ses mots est mal servi.
- Faute de frappe : 23 % de réponses différentes, cohérent avec un BM25 sensible à l'orthographe.

## 4. Écart entre langues (21 paires question FR / traduction AR)

| Mesure | Valeur |
|---|---:|
| Même premier article retrouvé | 0,619 |
| Même décision | 0,762 |
| Mêmes articles cités | 0,571 |
| Juste dans les deux langues / FR seulement / AR seulement | 11 / 6 / 3 |

Les réponses dépendent de la langue de la question : la même question obtient le bon article en
français mais pas en arabe dans 6 cas sur 21 (l'inverse dans 3 cas). Le cahier des charges demande
de traiter ce biais : piste, interroger aussi l'autre corpus via l'alignement AR ↔ FR et fusionner.

## 5. Correctif de l'abstention sans accents (20 novembre)

**Cause** (section 3) : la décision comparait la question telle que tapée aux articles accentués ;
sans accents, le cosinus d'e5 baissait juste sous le seuil français.

**Correctif** (`src/rag/recherche.py`, `src/rag/service.py`) : un second signal, le cosinus entre
question et articles **normalisés de la même façon** (français : sans accents, minuscules ; arabe :
diacritiques retirés, alif et ta marbuta unifiés). Le classement des articles ne change pas.
- **Français** : abstention si cosinus normalisé < 0,8567.
- **Arabe** : abstention si cosinus brut < 0,8217 **ou** cosinus normalisé < 0,8188. Le signal
  normalisé seul laissait passer une question hors périmètre (« شروط الحصول على رخصة اسلياقة »,
  permis de conduire avec faute de frappe : réponse hors sujet citant l'article 67) ; le dev ne
  contient que 3 questions arabes hors périmètre, trop peu pour régler un seuil arabe fiable.

Seuils réglés sur tout le dev par écriture (latine / arabe) ; en leave-one-out, le cosinus normalisé
donne 10 fausses abstentions contre 9 pour le brut sur les questions originales, et 3 contre 10 sur
leurs variantes sans accents ou à alif normalisé (`reports/gold/abstention/calibration_signal.json`).
Ce réglage utilise le dev déjà consulté : à confirmer sur des questions nouvelles.

**Audit complet relancé** (493 requêtes, 0 échec ; versions précédentes conservées dans
`avant_correctif_accents/` et `signal_normalise_seul/`) :

| Mesure | Silver | Normalisé seul | **Règle finale** |
|---|---:|---:|---:|
| Sans accents — décision identique / citations identiques | 0,500 / 0,444 | 1,000 / 0,889 | **0,944 / 0,833** |
| Alif normalisé — décision / citations | 0,909 / 0,727 | 1,000 / 0,818 | **1,000 / 0,818** |
| Faute de frappe — décision | 0,833 | 0,883 | 0,850 |
| Bruit de référence — décision | 0,974 | 0,974 | 0,974 |
| Français : fausse abstention finale / référence citée | 0,143 / 0,810 | 0,095 / 0,905 | **0,095 / 0,905** |
| Arabe traduit : fausse abstention finale / référence citée | 0,190 / 0,667 | 0,286 / 0,619 | 0,238 / 0,667 |
| Hors périmètre ayant reçu une réponse | 0,000 | 0,007 | **0,000** |
| Article inventé (avant / après filtre) | 0 / 0 | 0 / 0 | **0 / 0** |

Les écarts en arabe traduit viennent du LLM : la recherche y prend la même décision dans les trois
versions (fausse abstention de la recherche 0,095), c'est le LLM qui s'abstient ou non d'une
exécution à l'autre (bruit de référence : 2,6 % des décisions). La décision « sans accents » n'est
pas à 1,000 pour la même raison : la recherche est désormais identique par construction, le LLM non.
