# LegalTN : un assistant bilingue arabe-français sur le Code du travail tunisien, avec citations et abstention calibrée

*Rapport de niveau atelier — projet « NLP et spécialisation » — version du 21 novembre 2026*
*Auteure : Kawthar Jguirim. Brouillon : les sections marquées* **[À COMPLÉTER]** *dépendent de
l'étude d'utilité, qui n'a pas encore été menée.*

## Résumé

Nous construisons LegalTN, un assistant de questions-réponses sur le Code du travail tunisien en
arabe et en français. Il retrouve l'article pertinent (BM25 + embeddings e5, fusion RRF), cite
l'article et sa page, et **s'abstient** quand la question sort du Code. Nous publions (i) un
alignement article par article de 494 paires arabe-français, (ii) 200 phrases annotées en
obligations (qui, modal, quoi, quand), sans le texte intégral du Code, et (iii) une évaluation
de la fiabilité de l'abstention. Sur les questions neuves de l'étude, le système cite le bon
article pour 9 questions sur 9 auxquelles il répond et refuse les 2 questions hors Code ; il
s'abstient à tort pour 1 question sur 10. Aucun article inventé n'a été observé sur 326 réponses
générées. **Les annotations d'obligations sont des pré-annotations automatiques par un modèle de
langage, non encore relues par un humain ; l'étude d'utilité avec des étudiants est conçue mais
pas réalisée.**

## 1. Introduction

Un salarié, un étudiant ou un agent administratif cherche une règle précise (un délai, un plafond,
une exception) dans un texte long, dans une édition bilingue dont la version arabe est numérisée.
Trois risques sont propres à ce cadre : répondre à côté, **citer un article qui ne dit pas ce
qu'on lui fait dire**, et répondre alors que le Code est muet. Notre objectif est un système qui
cite, vérifie ses citations et sait refuser, et un jeu de ressources réutilisables pour le comparer.

Contributions : (1) un alignement AR/FR par embeddings validé sur 160 paires ; (2) un audit des
hallucinations et de la robustesse (accents, fautes, paraphrases, tunisien) ; (3) un jeu
d'obligations et un extracteur à base de règles ; (4) une calibration de l'abstention avec courbe
risque-couverture ; (5) le protocole, les outils et le script d'analyse d'une étude d'utilité.

## 2. Données

**Source.** Code du travail tunisien, édition bilingue (PDF, 291 pages), OCR puis segmentation :
515 articles arabes, 498 entrées françaises.

**Alignement.** 494 paires appariées (21 plages abrogées, 4 entrées hors Code). Méthode finale :
similarité LaBSE ou e5 plus un bonus de même numéro d'article (λ = 0,1), affectation hongroise.
Sur 160 paires vérifiées sur image : précision = rappel = **0,975** (embeddings seuls),
**1,000** (hybride) ; accord de 0,98 avec la numérotation du palier Bronze. *Biais* : les 160 paires
ont été tirées parmi les sorties de la numérotation, favorable à la méthode hybride.
Un audit des divergences (34 paires jugées) n'a trouvé **aucune divergence juridique réelle** entre
les versions, mais **8 articles dont le texte arabe numérisé contient une erreur qui change une
règle** (congé de maternité art. 64 : 0 et 5 jours au lieu de 30 et 15 ; art. 90, 425, 351…).

**Jeu d'obligations.** 300 phrases candidates choisies par la présence d'un marqueur modal (200 dev,
100 test gelé). Pour chacune : `qui`, `modal` (obligation / interdiction / permission), `quoi`,
`quand`, ou « non retenue » (définitions, renvois, règles sans action d'un rôle). Les 300 ont été
**pré-annotées par Claude (21/11/2026), statut `verifie_claude`** ; un outil de relecture
(`outils/annotateur_obligations.html`) passe chaque ligne en `verifie` après relecture humaine.
Répartition du dev : 114 obligations, 53 interdictions, 4 permissions, 29 non retenues ; du test :
28 obligations, 8 interdictions, **50 permissions**, 14 non retenues. **Le dev et le test n'ont pas
la même distribution** (le dev ne permet pas d'évaluer la détection des permissions). Trois phrases du
test sont des quasi-doublons de phrases du dev (même article), et 46 articles figurent dans les deux
jeux : le découpage ne garantit pas l'indépendance par article.

**Évaluation de l'extracteur (dev, pré-gold Claude).** Détection d'obligation F1 0,94 ; type
(obligation, interdiction) F1 0,98–0,99 ; **F1 par rôle** (11 classes) : exactitude 0,62, F1 macro
0,34 — le type est trouvé, le rôle rarement, car il n'est pas nommé dans 101 phrases sur 164 (voix
passive, sujet implicite). Le dev ayant été annoté avec les prédictions sous les yeux, ces chiffres
sont probablement surestimés ; le test n'est pas encore mesuré.

**Références croisées.** Extraction à base de règles, en français et en arabe (176 et 145 mentions :
articles cités, plages, sous-articles, relatifs « l'article précédent », textes externes).
Précision estimée à 91 % sur 35 mentions relues par Claude (pas de gold humain, rappel non mesuré).
Le contrôle automatique des cibles et la **comparaison arabe/français des renvois** (68 entrées sur
102 identiques) révèlent des défauts d'OCR du texte arabe non vus ailleurs (art. 87, 100, 125, 176,
227, 265, 287), à confirmer sur image. Détail : `reports/platinum/references/RESULTATS.md`.

**Publication.** Le dossier `data/publication/legaltn_v1/` contient l'alignement (sans texte),
les obligations dev (la phrase est remplacée par son empreinte), les questions de développement, une
fiche de données et des empreintes. Il **ne contient ni le texte des articles ni le test des
obligations** : la licence de l'édition source n'est pas clarifiée (`LICENCE.md`), et publier les
étiquettes du test avant sa mesure unique l'invaliderait.

## 3. Système et audit

**Recherche.** BM25 + e5-base, fusion RRF (k = 60), abstention par seuil sur le cosinus maximal
(signal normalisé : sans accents, alif unifié). Réponse rédigée par qwen2.5:3b en **citation
forcée** : toute citation absente des extraits fournis est bloquée. Sur le dev (77 questions),
R@1 est de 1,00 en français et 0,62 en arabe traduit (BM25 seul : 0,95 et 0,52).

**Audit (493 requêtes, 326 réponses générées).** **0 article inventé** affiché, **0 question
hors Code ayant reçu une réponse**. Robustesse : la décision reste identique dans 94 % des cas
quand on retire les accents (50 % avant le correctif du signal d'abstention), 57 % pour une
paraphrase, contre un bruit de référence de 97 % (le LLM n'est pas déterministe). Entre le français
et sa traduction arabe, la réponse est juste dans les deux langues pour 12 questions sur 21. Les questions en
dialecte tunisien latinisé sont mal traitées par la recherche directe (R@5 0,03) ; les traduire
vers le français avec qwen2.5:7b avant la recherche donne R@5 0,50.

**Fidélité.** Un LLM-juge (qwen2.5:7b) compare chaque réponse aux articles cités : κ = 0,45
avec les verdicts de Claude, **13 réponses infidèles sur 13 signalées**, mais 6 fausses alertes
sur 32 réponses fidèles. Il sert de filtre, pas de juge ; sa validation humaine reste à faire.

## 4. Abstention calibrée

Règle de la démo : on s'abstient si le cosinus normalisé du meilleur article est sous un seuil par
écriture (français 0,8567 ; arabe 0,8188, ou cosinus brut arabe sous 0,8217). Les seuils ont été
réglés sur le dev ; nous mesurons donc la règle (a) sur le dev, (b) en leave-one-out, (c) sur
**12 questions neuves** écrites pour l'étude d'utilité, absentes du dev.

| Jeu | n | Décision juste | IC 95 % | Fausses abstentions | Hors Code répondu |
|---|---:|---:|---|---:|---:|
| Dev (seuils réglés dessus) | 77 | 0,805 | [0,71 ; 0,88] | 8 / 48 | 1 / 29 |
| Dev, leave-one-out | 77 | 0,740 | [0,65 ; 0,83] | 10 / 48 | 4 / 29 |
| **12 questions neuves** | 12 | **0,917** | [0,75 ; 1,00] | 1 / 10 | **0 / 2** |

« Décision juste » : répondre avec le bon article en tête si la question est dans le Code,
s'abstenir sinon. Sur les 12 questions neuves, **9 réponses données, 9 avec le bon article** ; la
fausse abstention est une question sur l'interdiction des heures supplémentaires pour un mineur
(cosinus 0,849, seuil 0,857). Sur le dev, 6 des 8 fausses abstentions sont des questions en tunisien
latinisé (refusées par construction) et 2 des traductions arabes ; **aucune question française**.

**Pouvoir discriminant.** L'AUROC du signal pour distinguer « dans le Code » de « hors Code » est de
0,82 en français et 0,87 en arabe (dev). **Courbe risque-couverture** (le « risque » compte les
réponses fausses et les réponses à des questions hors Code) : en ne répondant qu'au quart des
questions au signal le plus élevé, le risque est de 5 % ; à la moitié, 24 % ; en répondant à tout,
56 %. Le signal est donc informatif, mais **à couverture élevée il laisse passer beaucoup d'erreurs** :
un seuil seul ne suffit pas pour un usage où une réponse fausse coûte cher.

**Limites.** Les seuils sont réglés sur un dev déjà consulté ; 12 questions neuves ne donnent qu'un
intervalle large ; la détection hors Code repose sur 29 questions dont 3 en arabe.

## 5. Étude d'utilité **[À COMPLÉTER]**

**Protocole (prêt)** : `etude_utilite/PROTOCOLE.md`. Plan croisé : chaque étudiant (droit ou
administration, cible 12 à 20) répond à 2 séries de 6 questions, l'une avec LegalTN, l'autre avec le
Code en PDF et la recherche par mot-clé ; 4 groupes équilibrent condition et ordre. Les 12 questions
(`etude_utilite/taches_v1.csv`) sont neuves ; 2 sont hors Code. Mesures : exactitude, bon article cité,
absence de réponse reconnue, temps, confiance et calibration de la confiance, SUS, préférence.
Outils : page de passation `outils/etude_utilite.html` (testée par un parcours simulé), script
d'analyse `src/etude/analyser.py` (différence appariée, intervalle bootstrap, test de permutation ;
testé sur données simulées).

**Résultats** : _non disponibles — aucune passation n'a eu lieu._ Cette section doit recevoir
`reports/platinum/etude_utilite/RESULTATS.md` après passation et notation. Hypothèses fixées à l'avance :
H1 exactitude plus élevée avec LegalTN ; H2 temps plus court ; H3 meilleure reconnaissance du hors
Code ; H4 (exploratoire) confiance mieux calibrée.

## 6. Limites et éthique

- **Annotations par un modèle de langage** (obligations, divergences, paraphrases, traductions,
  jugements de fidélité) : un seul « annotateur », non encore relu ; aucun kappa inter-humains.
- Dev consulté pour régler les seuils ; échantillons petits ; modèles locaux (qwen2.5 3b/7b)
  non déterministes.
- Texte arabe numérisé avec des erreurs qui changent des règles (8 articles) : une réponse
  arabe citant ces extraits peut afficher un chiffre faux.
- Le Code a été modifié depuis cette édition ; **LegalTN n'est pas un conseil juridique**.
- Étude : consentement, pseudonymisation, retrait possible ; aucune donnée personnelle.

## 7. Reproductibilité

Environnement `. .\env_silver.ps1` ; tests `python -m pytest -q`. Commandes par résultat :
alignement `src.alignement_embeddings.evaluer` ; audit `src.audit.audit` ; obligations
`src.obligation_extraction.appliquer_annotations` puis `evaluer_obligations` ; abstention
`src.platinum.calibration` ; publication `src.publication.preparer` ; étude `src.etude.analyser`.
Journal détaillé : `experiments.md`.

## Annexe — état des exigences du palier Platinum

| Exigence | État | Ce qui manque |
|---|---|---|
| Corpus aligné publié | **Prêt à publier** (alignement sans texte) | Clarifier la licence ; publier (par l'auteure) ; corriger les 8 articles arabes |
| Jeu d'obligations publié | **Prêt (dev)** : pré-annoté par Claude | Relecture humaine des 300 lignes ; mesure unique sur le test, puis publication du test |
| Abstention calibrée | **Fait** (courbe risque-couverture, LOO, 12 questions neuves) | Plus de questions neuves, surtout hors Code et en arabe |
| Étude d'utilité avec étudiants | **Conçue, non réalisée** | Recruter, passer, noter, analyser |
| Rapport niveau atelier | **Brouillon** (ce document) | Section 5, relecture, mise en forme |
