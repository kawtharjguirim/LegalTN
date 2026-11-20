# Démonstration — validation du palier Silver (LegalTN)

Durée visée : **10 à 12 minutes**. Chaque résultat attendu ci-dessous a été obtenu sur
l'application réelle le 16 novembre 2026 (qwen2.5:3b, RTX 2050). Les réponses du LLM peuvent
varier légèrement d'une formulation à l'autre ; les articles cités sont stables.

Correspondance avec les exigences du mail de validation :

| Exigence | Où dans la démo |
|---|---|
| Modèles appris (encodeurs, fine-tuning) | Étape 5 (NER fine-tuné) + étape 2 (encodeur e5) |
| LLM et prompting | Étapes 2–4 (réponse rédigée, citation forcée) + tableau étape 6 |
| RAG et recherche sémantique | Étapes 2–3 (hybride BM25 + e5, étapes visibles) |
| Résultats, baselines, ablations | Étape 6 (4 tableaux) |
| Démonstration fonctionnelle | Toute la démo |

---

## 0. Préparation (la veille et 10 minutes avant)

**La veille, une seule fois** (si `models\ner\` n'existe pas) :

```powershell
. .\env_silver.ps1
& $Py -X utf8 -m src.ner_juridique.entrainer --langue fr --modeles xlmr --graines 13 --sauver models/ner
& $Py -X utf8 -m src.ner_juridique.entrainer --langue ar --modeles arabert --graines 13 --sauver models/ner
```

**⚠️ Avant tout : libérer au moins 10 Go sur le disque C.** Le 20 novembre, avec C plein
(0,2 Go libres), Windows n'a plus pu agrandir son fichier d'échange : le serveur de démo, Chrome et
le NER ont planté par manque de mémoire (« fichier de pagination insuffisant », « Segmentation
fault »). Une démo en direct sur cette machine dans cet état n'est pas fiable.

**10 minutes avant** : fermer les applications lourdes (la carte graphique n'a que 4 Go), puis

```powershell
cd D:\LegalTN\LegalTN-silver
.\demo_silver.ps1
```

Le script vérifie Python, la carte graphique, Ollama (il le démarre au besoin), qwen2.5:3b, les
modèles NER, préchauffe le LLM puis ouvre http://127.0.0.1:18765/. Toutes les lignes doivent être
`[OK]`. Ouvrir aussi un second terminal PowerShell (`. .\env_silver.ps1`) pour l'étape 5.

Garder ouverts dans l'éditeur : `reports/silver/alignement/RESULTATS.md`,
`reports/silver/rag/RESULTATS.md`, `reports/silver/ner/RESULTATS.md`, `reports/silver/llm/RESULTATS.md`.

---

## 1. Introduction (1 min) — page d'accueil

> « LegalTN répond à des questions sur le Code du travail tunisien, en français et en arabe, en
> citant l'article exact — ou en s'abstenant. Au palier Bronze, la recherche était lexicale (BM25).
> Au Silver, nous avons ajouté des encodeurs appris, un RAG dense bilingue, un LLM local avec
> citation vérifiée, et un NER fine-tuné. »

Montrer le panneau « Corpus indexé » : 496 articles FR, 491 AR, statut en ligne.

## 2. Question française : la chaîne complète (2 min)

Cliquer **Recherche juridique** et poser :

> **Quelles sont les attributions des conseils de prud'hommes ?**

Attendu :
- **Réponse rédigée** (qwen2.5:3b) : les conseils de prud'hommes règlent les différends individuels
  nés des contrats de travail ou d'apprentissage… `[Article 183]`.
- Articles : **183**, 191, 184.
- Déplier **Étapes du traitement** : langue français → BM25 → dense e5 (similarité 0,880, seuil
  0,860) → fusion RRF → citation article 183 → rédaction LLM, citation vérifiée.

> « Le moteur Bronze (BM25 seul) répondait l'article 182 : faux. La recherche hybride trouve le
> bon article. Chaque étape est visible, et le serveur vérifie que l'article cité par le LLM fait
> bien partie des extraits — sinon la réponse est remplacée par une abstention. »

Déplier **Version arabe** sous l'article 183 : la citation est bilingue (même article, page AR).

## 3. Question arabe (1 min 30)

Basculer l'interface en **العربية** (en haut à droite), poser :

> **في أي الحالات لا ينطبق تحجير العمل الليلي على النساء؟**

Attendu : réponse rédigée **en arabe** (force majeure, matières périssables, postes de direction ou
techniques, services sociaux…) `[Article 68]` ; articles **68**, 71, 69 ; version française dépliable.

> « BM25 répondait l'article 29. En arabe, la recherche hybride gagne 10 points de rappel@1 sur
> BM25 (0,62 contre 0,52), et le LLM répond dans la langue de la question dans 100 % des cas. »

Option : bouton **Résumé en langage clair** sous l'article 68 (≈ 3 s).

## 4. Abstention et limites honnêtes (2 min)

Revenir en **FR** et poser successivement :

| Question | Attendu | Message |
|---|---|---|
| **Quelle est la capitale de la Tunisie ?** | Abstention (similarité 0,796 < 0,860) | Hors périmètre : refus plutôt qu'invention. 100 % des questions hors périmètre du dev refusées. |
| **Quel est le délai de préavis pour rompre un CDI ?** | Abstention **à tort** (0,856, juste sous 0,860) | Limite connue : le sigle « CDI » n'apparaît pas dans le Code. Piste : expansion des sigles. |
Puis **le dire, sans le jouer en direct** (la réponse du LLM à cette question n'est pas stable
d'une exécution à l'autre, voir « Questions probables ») :

> « Une citation correcte ne garantit pas une réponse fidèle. À la question “Un congé payé de cinq
> jours ouvrables peut-il être fractionné ?”, le LLM a cité le bon article, le 118, mais a répondu
> “oui” alors que l'article impose un congé continu en dessous de six jours. Nos métriques
> automatiques vérifient la citation, pas le fond : c'est l'objet du LLM-juge au palier Gold. »

C'est un atout : cela prouve l'analyse critique des résultats.

## 5. NER fine-tuné en direct (1 min 30) — second terminal

D'abord une phrase classique, où règles et modèle sont d'accord :

```powershell
& $Py -X utf8 -m src.ner_juridique.predire "L'employeur doit informer l'inspection du travail dans un délai de quinze jours et verser une amende de 300 dinars."
```

```text
Règles        : [L'employeur]ROLE doit informer [l'inspection du travail]INSTITUTION [dans un délai de quinze jours]DELAI et verser une amende de [300 dinars]MONTANT.
fr_xlmr       : [L'employeur]ROLE doit informer [l'inspection du travail]INSTITUTION [dans un délai de quinze jours]DELAI et verser une amende de [300 dinars]MONTANT.  (≈ 600 ms)
```

Puis **la généralisation** : le modèle reconnaît des rôles absents des listes de mots des règles.

```powershell
& $Py -X utf8 -m src.ner_juridique.predire "Les stagiaires ne peuvent être employés plus de six heures par jour."
& $Py -X utf8 -m src.ner_juridique.predire "يجب على مدير الشركة التصريح بكل متربص لدى الصندوق في أجل ثمانية أيام."
```

```text
Règles        : Les stagiaires ne peuvent être employés plus de [six heures par jour]MONTANT.
fr_xlmr       : [Les stagiaires]ROLE ne peuvent être employés plus de [six heures par jour]MONTANT.
Règles        : يجب على مدير الشركة التصريح بكل متربص لدى الصندوق [في أجل ثمانية أيام]DELAI.
ar_arabert    : يجب على [مدير الشركة]ROLE التصريح بكل متربص لدى الصندوق [في أجل ثمانية أيام]DELAI.
```

> « Le modèle n'est pas une copie des règles : entraîné sur leurs annotations, il reconnaît
> “les stagiaires” ou “مدير الشركة” comme rôles, alors qu'aucune règle ne les contient. »

Limite à mentionner si on vous la demande : il manque encore « chaque stagiaire » → « متربص »
en arabe, et « المدير الجهوي » est découpé à tort en deux INSTITUTION.

> « Faute de corpus juridique annoté, nous avons pré-annoté par règles 790 phrases FR et 970 AR,
> puis fine-tuné trois encodeurs sur 3 graines. En français XLM-R est le meilleur et le plus
> stable ; en arabe le modèle monolingue AraBERT l'emporte. Les 4 lots de 60 phrases corrigés à la
> main serviront de gold. »

## 6. Résultats et ablations (2 min) — fichiers RESULTATS.md

**Alignement AR ↔ FR (160 paires vérifiées sur image)**

| Système | Précision = rappel |
|---|---:|
| Numéro seul (naïf) | 0,894 |
| LaBSE, sans en-tête numéroté | 0,975 |
| e5, sans en-tête | 0,975 (0,956 avec normalisation AR : ablation défavorable) |
| Hybride embeddings + numéro | **1,000** |

**Recherche (77 questions dev)** — R@1

| Système | FR | AR | Fausses abstentions |
|---|---:|---:|---:|
| BM25 (Bronze) | 0,95 | 0,52 | 7 |
| Hybride e5, seuil global | 1,00 | 0,62 | 21 |
| **Hybride e5, seuil par langue** | **1,00** | **0,62** | **3** |

**LLM, 3 stratégies de prompting**

| Stratégie | Article de référence cité | Citation inventée | Abstention à tort |
|---|---:|---:|---:|
| zero-shot | 0,542 | 0,028 | 0,250 |
| few-shot | 0,625 | 0,023 | 0,083 |
| **citation forcée** | **0,667** | **0,000** | 0,167 |

**NER — F1 strict sur 120 phrases dev (pré-gold annoté par Claude, pas encore relu par un humain)**

| | Règles | CRF (Bronze) | Fine-tuné |
|---|---:|---:|---:|
| FR | 0,423 | 0,406 | **XLM-R 0,479** (souple 0,644) |
| AR | **0,484** | 0,364 | AraBERT 0,416 (souple 0,568) |

Message : l'accord avec les règles (XLM-R FR 0,886) surestimait la qualité ; les modèles héritent
des oublis des règles. En français, XLM-R les dépasse ; en arabe, pas encore.

Messages clés : l'en-tête numéroté est un raccourci (100 % trivial) ; seuil d'abstention par
langue indispensable ; la citation forcée supprime les citations inventées mais augmente les refus ;
classement des encodeurs inversé entre FR et AR.

## 7. Conclusion et suite (30 s)

> « Reste à faire : F1 NER sur gold (annotation en cours), notation humaine des 40 résumés,
> validation des questions arabes traduites ; au Gold : questions en tunisien (0/6 aujourd'hui,
> l'arabizi n'est pas compris), LLM-juge pour la fidélité, divergences AR/FR (AR-52, AR-335). »

---

## Plan B

| Problème | Solution |
|---|---|
| Le NER plante à l'étape 5 (« Segmentation fault », mémoire insuffisante) | Montrer les sorties réelles enregistrées : `reports/silver/capsule/ner_sorties_reference.json`, ou le plan NER de la capsule. |
| Ollama ne répond pas | La démo affiche les extraits seuls et l'indique dans les étapes : continuer, montrer le tableau LLM. |
| Carte graphique saturée / lente | Fermer le navigateur lourd ; relancer `demo_silver.ps1`. |
| Application qui ne démarre pas | Démo Bronze sans dépendances : `.\demarrer.ps1 -Port 18766 -Moteur bm25`. |
| Plus rien ne marche | Lancer la **capsule vidéo** `reports/silver/capsule/capsule_silver_legaltn.mp4` (1 min 58, sous-titrée en français), puis montrer `reports/silver/*/RESULTATS.md`. |

**Capsule vidéo** : régénérable sur l'application réelle (serveur hybride lancé sur le port 18765) :
`& $Py -X utf8 -m src.rapports.generer_capsule_silver`. Le fichier `.srt` à côté permet de
charger les sous-titres séparément (VLC : Sous-titres → Ajouter un fichier).

## Questions probables du jury

- **Pourquoi un LLM de 3 milliards de paramètres ?** 4 Go de VRAM ; local, gratuit, reproductible
  (température 0) ; les textes ne sortent pas de la machine.
- **Pourquoi geler les embeddings ?** Ceux de XLM-R (192 M paramètres) saturaient les 4 Go :
  38 min par graine ; gelés : 4 min, sans perte (CamemBERT 0,846 gelé contre 0,833).
- **Les seuils sont-ils réglés sur le test ?** Non : réglés en leave-one-out sur le dev ; aucun jeu
  de `data/test_locked/` n'a servi.
- **Le gold d'alignement est-il biaisé ?** Oui, tiré parmi les sorties de la numérotation : c'est
  pourquoi nous mesurons aussi les embeddings sans en-tête numéroté.
- **Les F1 NER sont-ils fiables ?** Ce sont des accords avec les règles, pas une qualité : le gold
  (4 × 60 phrases) est en cours d'annotation.
- **Le LLM est-il déterministe ?** Non, malgré la température 0 : sur la question du congé
  fractionné, nous avons obtenu « oui », « non » puis une abstention selon l'exécution (calculs
  GPU et cache de prompts d'Ollama). Au sein d'une même session la réponse est stable, et les
  questions de la démo ont donné la même réponse sur 3 essais. Les mesures LLM sont donc une
  exécution unique : à répéter pour estimer leur variance.

## Résultats de la répétition (16 novembre 2026)

Lancement par `demo_silver.ps1` : toutes les vérifications `[OK]` (Python, RTX 2050, Ollama,
qwen2.5:3b, modèles NER, préchauffage), application prête ≈ 25 s après.

| Étape | Question | Obtenu | Stabilité |
|---|---|---|---|
| 2 | Attributions des conseils de prud'hommes | Article 183 + réponse rédigée, 3,4 s | 3/3 identiques |
| 3 | تحجير العمل الليلي على النساء | Article 68 + réponse arabe, 2,2 s | 3/3 identiques |
| — | Rupture abusive (question de secours FR) | Article 23 + réponse rédigée | 3/3 identiques |
| 4 | Capitale de la Tunisie | Abstention (0,796) | déterministe (recherche) |
| 4 | Préavis d'un CDI | Abstention à tort (0,856) | déterministe (recherche) |
| 5 | NER : 3 phrases | Sorties identiques à celles ci-dessus, ≈ 0,6 s par phrase | modèle fixe |
| — | Congé fractionné | « oui », puis « non », puis abstention ×6 | **instable : retirée du scénario** |
