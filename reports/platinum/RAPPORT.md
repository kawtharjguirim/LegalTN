# LegalTN : un assistant bilingue arabe-français sur le Code du travail tunisien, avec citations et abstention calibrée

*Rapport de niveau atelier — projet « NLP et spécialisation » — version du 21 novembre 2026*
*Auteure : Kawthar Jguirim. **Brouillon étoffé** : la section 8 (étude d'utilité) attend des participants, et la
plupart des références d'évaluation sont des annotations de Claude non encore relues par un humain (section 10).*

## Résumé

Nous construisons LegalTN, un assistant de questions-réponses sur le Code du travail tunisien en arabe et en français.
Il retrouve l'article pertinent (BM25 et embeddings e5, fusion RRF), cite l'article et sa page, et **s'abstient** quand la
question sort du Code. Le projet produit : (i) un alignement article par article de 494 paires arabe-français ; (ii) un
jeu de 300 phrases annotées en obligations (qui, modal, quoi, quand), avec un extracteur à base de règles ; (iii) une
extraction des références croisées dans les deux langues ; (iv) une classification de domaine des articles avec transfert
entre langues et fine-tuning LoRA ; (v) une évaluation de la fiabilité de l'abstention et de la robustesse du système ;
(vi) 20 corrections du texte arabe numérisé, dont 13 lues sur l'image du PDF ; (vii) le protocole et les outils d'une étude
d'utilité. Sur 12 questions neuves, le système cite le bon article pour 9 questions sur 9 auxquelles il répond et refuse
les 2 questions hors Code ; il s'abstient à tort pour 1 question sur 10. Aucun article inventé n'a été observé sur 326
réponses générées. **Limites principales** : les annotations d'obligations, de NER, de divergences et les jugements de
fidélité sont des pré-annotations de Claude non relues ; l'étude avec des étudiants est conçue mais pas réalisée ; la
publication attend la clarification d'une licence.

## 1. Introduction

Un salarié, un étudiant ou un agent administratif cherche une règle précise (un délai, un plafond, une exception) dans un
texte long, dans une édition bilingue dont la version arabe est numérisée. Trois risques sont propres à ce cadre :
répondre à côté, **citer un article qui ne dit pas ce qu'on lui fait dire**, et répondre alors que le Code est muet. Les
réponses peuvent aussi dépendre de la langue de la question, ce qui est un biais à mesurer plutôt qu'à ignorer.

Notre objectif est un système qui cite, vérifie ses citations et sait refuser, accompagné de ressources réutilisables pour
le comparer à d'autres. Le texte est une source publique et le système ne fournit qu'une information, jamais un conseil
juridique.

**Contributions.** (1) Un alignement arabe/français par embeddings, validé sur 160 paires. (2) Un audit des hallucinations
et de la robustesse (accents, fautes, paraphrases, dialecte tunisien). (3) Un jeu d'obligations et un extracteur, avec un
F1 par rôle. (4) L'extraction des références croisées et un contrôle de cohérence entre les deux langues qui révèle des
défauts d'OCR. (5) Une classification de domaine des articles, avec transfert FR ↔ AR et LoRA. (6) Une calibration de
l'abstention avec courbe risque-couverture. (7) Un protocole d'étude d'utilité avec ses outils.

## 2. Travaux liés et outils

Nous ne faisons pas de revue de la littérature juridique ; nous nous appuyons sur des composants connus :
BM25 pour la recherche lexicale ; **multilingual-e5** (Wang et al., 2022) et **LaBSE** (Feng et al., 2022) pour les
embeddings multilingues ; **XLM-R** (Conneau et al., 2020), **CamemBERT** (Martin et al., 2020) et **AraBERT**
(Antoun et al., 2020) pour le NER ; **LoRA** (Hu et al., 2021) pour le fine-tuning à faible coût ; le **kappa de Cohen**
(Cohen, 1960) pour l'accord ; la fusion **RRF** (Cormack et al., 2009). La génération utilise qwen2.5 (3B et 7B) servi
localement par Ollama. Aucun service payant n'est utilisé.

## 3. Données

**Source.** Code du travail tunisien, édition bilingue (PDF de 291 pages), numérisée par OCR puis segmentée : 515
articles arabes et 498 entrées françaises. Les numéros d'articles et les pages renvoient à ce PDF.

### 3.1 Alignement arabe/français

494 paires appariées (21 plages abrogées, 4 entrées hors Code). Méthode finale : similarité LaBSE ou e5 plus un bonus de
même numéro d'article (λ = 0,1), affectation hongroise. Sur 160 paires vérifiées sur image : précision et rappel de
**0,975** pour les embeddings seuls, **1,000** pour l'hybride ; la numérotation seule, sans gestion des suffixes, obtient
0,894. L'accord avec la numérotation du palier Bronze est de 0,98. *Biais* : les 160 paires ont été tirées parmi les sorties
de la numérotation, ce qui avantage la méthode hybride.

### 3.2 Texte arabe numérisé et corrections

Un audit des divergences (34 paires jugées par Claude) n'a trouvé **aucune divergence juridique réelle** entre les deux
versions : tout vient de la numérisation. Un détecteur combinant la similarité LaBSE et l'écart de nombres (en chiffres et
en lettres, FR et AR) signale 11 paires faibles sur 12 et 9 écarts de nombres sur 12 comme défauts, contre 0 sur 10 paires
tirées au hasard. Huit articles arabes contenaient une erreur qui change une règle ; nous avons vérifié sur l'image de la
page et corrigé **20 passages dans 14 articles** (13 lus sur image, 7 déduits du texte français et à confirmer) : le congé
de maternité (art. 64 : 30 et 15 jours, et non « 0 » et « 5 »), les taux des heures supplémentaires (art. 90 : 75 %, 25 %,
50 %), l'amende de l'article 425 (72 à 288 dinars), le délai de 3 mois de l'article 351, la liste des articles sanctionnés de
l'article 234 et les renvois de l'article 287. Le fichier d'origine est conservé ; un fichier corrigé est utilisé par la
recherche et l'extraction des références.

### 3.3 Obligations

300 phrases candidates choisies par la présence d'un marqueur modal (200 pour le développement, 100 pour un test gelé).
Pour chacune : le rôle (`qui`), le type (`obligation`, `interdiction`, `permission`), l'action (`quoi`) et la condition
(`quand`), ou « non retenue » (définitions, renvois, règles sans action d'un rôle). Les 300 ont été **pré-annotées par
Claude, statut `verifie_claude`** ; un outil de relecture fait passer chaque ligne en `verifie` après contrôle humain.
Répartition : dev 114 obligations, 53 interdictions, 4 permissions, 29 non retenues ; test 28, 8, **50**, 14. Les deux jeux
n'ont donc pas la même distribution, trois phrases du test sont des quasi-doublons de phrases du dev et 46 articles
figurent dans les deux : l'indépendance par article n'est pas garantie.

### 3.4 Questions

56 questions de développement (44 en français, 9 en tunisien, 3 en arabe ; 27 dans le Code, 29 hors du Code), 21
traductions arabes, 30 questions en tunisien et 42 paraphrases, un jeu de test gelé de 40 questions, et 12 questions
neuves écrites pour l'étude d'utilité. Les traductions, paraphrases et questions tunisiennes sont de Claude, à valider.

### 3.5 Étiquettes de domaine

Les articles sont étiquetés en 12 domaines (contrat de travail, durée-repos-congés, salaire, conflits et juridictions, etc.)
d'après la **structure du Code** : le texte français place l'intitulé du chapitre suivant à la fin de l'article qui
précède. 17 bornes sur 17 sont confirmées par un intitulé français et 15 par la hiérarchie arabe. Le regroupement des
chapitres en 12 domaines est une décision de conception, non validée par un juriste.

## 4. Système

**Recherche.** BM25 et e5-base (préfixes « query: » et « passage: »), fusion RRF (k = 60) ; le classement dense peut
s'étendre à l'autre langue avec un poids (section 9). **Abstention.** On s'abstient si le cosinus maximal est sous un
seuil par écriture, sur un signal **normalisé** (sans accents, alif unifié), pour ne pas dépendre de la façon de taper la
question. **Génération.** qwen2.5:3b en **citation forcée** : la réponse doit citer des articles fournis, toute citation
hors contexte est bloquée et la réponse devient une abstention. **Résumé** en langage clair par article. **Application.**
Une API HTTP locale, une interface de démonstration, et un **tableau de bord d'évaluation** qui lit les résultats des
rapports et indique, pour chaque bloc, la nature de la référence (humaine, Claude non relue, automatique).

## 5. Expériences de modélisation

### 5.1 Recherche et génération

Sur 77 questions de développement, l'hybride e5 avec seuil par langue atteint un R@1 de 1,00 en français et 0,62 en
arabe traduit (BM25 seul : 0,95 et 0,52). Avec qwen2.5:3b, la citation forcée donne : référence citée 0,667, citation
inventée 0,000 et abstention à tort 0,167, contre 0,542, 0,028 et 0,250 en zero-shot et 0,625, 0,023 et 0,083 en
few-shot (plafond de la recherche : 0,812). Le dev a servi à régler les seuils : ces chiffres sont indicatifs.

### 5.2 Reconnaissance d'entités (NER)

Quatre types : ROLE, INSTITUTION, DELAI, MONTANT. Sur le corpus silver (accord avec les règles), XLM-R atteint 0,886 en
français et AraBERT 0,761 en arabe. Contre un **pré-gold de Claude** de 120 phrases, le F1 strict / souple tombe à :
français, règles 0,423 / 0,620, CRF 0,406 / 0,580, XLM-R 0,479 / 0,644 ; arabe, règles 0,484 / 0,603, CRF 0,364 / 0,462,
AraBERT 0,416 / 0,568. L'accord avec les règles surestimait donc nettement la qualité ; XLM-R généralise en français,
AraBERT peu en arabe. Le pré-gold n'est pas relu.

### 5.3 Obligations : détection, type et rôle

Sur le dev (pré-gold de Claude, annoté avec les prédictions de l'extracteur sous les yeux, donc probablement surestimé) :
détection d'obligation F1 0,94 ; type F1 0,986 (obligation), 0,981 (interdiction), 0,889 (permission, 4 cas). Le
**F1 par rôle** (11 classes : employeur, salarié, apprenti, maître, administration, juridiction, organisation, parties,
toute personne, autre, aucun) donne une exactitude de 0,62 et un F1 macro de 0,34 : employeur 0,51, salarié 0,42,
administration 0,40, juridiction 0,80. L'extracteur trouve le type mais rarement le rôle : celui-ci n'est pas nommé dans
101 phrases sur 164 (voix passive, sujet implicite), et l'extracteur en attribue un dans 24 de ces cas. Le test n'est pas
mesuré (il ne se mesure qu'une fois, après relecture).

### 5.4 Références croisées

Extraction à base de règles (articles cités, listes, plages, sous-articles, renvois relatifs « l'article précédent »,
textes externes) en français (176 mentions) et en arabe (147). Précision estimée à 91 % sur 35 mentions relues par Claude
(un premier échantillon de 45 a servi à corriger les règles) ; le rappel n'est pas mesuré. Le **contrôle de cohérence
arabe/français** compare les renvois des deux versions d'un même article : avant correction du texte arabe 68 des 102
entrées à renvois étaient identiques, après 75 (73,5 %). Ce contrôle a servi à **trouver** des défauts d'OCR (renvois « 0 »,
« 2779 », « 2854 », « 5 » pour 95…), qui ont ensuite été corrigés : les renvois croisés sont un outil de contrôle du corpus.

### 5.5 Classification de domaine

Prédire le domaine d'un article (12 classes) d'après son texte. Validation croisée **par blocs** de 6 articles voisins
(les voisins se ressemblent), français et arabe dans le même pli, 5 plis, 3 graines. Macro-F1 : majorité 0,02 ;
TF-IDF 0,58 (FR) et 0,61 (AR) ; e5 et régression logistique 0,63 et 0,60 ; l'ajout de l'autre langue à l'apprentissage ne
sert pas ; **transfert** appris en français testé en arabe 0,41, appris en arabe testé en français 0,41. Le **fine-tuning LoRA**
d'e5 (rang 8) atteint 0,715 ± 0,012 en français et 0,642 ± 0,021 en arabe, et 0,46 (FR → AR) et 0,53 (AR → FR) en transfert. Les domaines
définis par leur place plutôt que par leur sujet (inspection et sanctions, statuts particuliers) sont les plus difficiles
(F1 de 0,4 à 0,55) ; conflits et juridictions (0,86) et durée-repos-congés (0,81) sont les plus faciles.

### 5.6 Questions en dialecte tunisien

Sur 30 questions dans le Code et 9 hors du Code, la détection de l'arabizi est exacte (100 %, sans faux positif). R@5 :
recherche directe 0,17 ; multilingue direct 0,03 ; translittération 0,10 ; **traduction en français puis recherche** 0,40
avec qwen2.5:3b et **0,50 avec qwen2.5:7b** (R@1 0,27). Traduire puis chercher bat la recherche multilingue directe ; le
français est un meilleur pivot que l'arabe standard (0,23) ; la taille du LLM compte. Les traductions de la derja restent
souvent fausses, et 2 questions hors Code sur 9 reçoivent une réponse avec le 7B.

## 6. Audit : hallucinations et robustesse

**Hallucinations** (493 requêtes, 326 réponses du LLM, aucun appel en échec) : **0 article inventé** affiché ; 1,8 % de
citations hors des extraits fournis avant filtre, toutes bloquées ; 12 % de réponses sans citation avant filtre ; **0
question hors Code ayant reçu une réponse**.

**Robustesse (décision identique à celle de la question d'origine)** : bruit de référence du LLM 0,974 ; sans accents 0,944
(0,500 avant le correctif du signal d'abstention) ; minuscules 0,905 ; politesse ajoutée 0,882 ; faute de frappe 0,850 ;
sans ponctuation 0,929 ; alif normalisé 1,000 ; **paraphrase 0,571**, le point le plus faible : la recherche dépend du
vocabulaire du texte de loi.

**Fidélité (LLM-juge).** qwen2.5:7b juge si une réponse est fidèle aux articles qu'elle cite. Contre les verdicts de Claude
sur 56 réponses, κ = 0,45 (0,46 en fidèle/non fidèle) ; il signale **13 réponses infidèles sur 13** mais produit 6 fausses
alertes sur 32 réponses fidèles et distingue mal « partiel ». qwen2.5:3b n'est pas utilisable (κ = 0,15, 5 infidèles
validées). Une première consigne produisait 32 verdicts illisibles sur 56 ; la consigne a été corrigée après avoir vu ces
résultats, ce qui rend les chiffres légèrement optimistes. La validation contre un humain reste à faire.

## 7. Abstention calibrée

Règle de la démonstration : on s'abstient si le cosinus normalisé du meilleur article est sous un seuil par écriture
(français 0,8567 ; arabe 0,8188, ou cosinus brut arabe sous 0,8217). Les seuils ont été réglés sur le dev ; nous mesurons la
règle (a) sur le dev, (b) en leave-one-out, (c) sur **12 questions neuves**, absentes du dev.

| Jeu | n | Décision juste | IC 95 % | Fausses abstentions | Hors Code répondu |
|---|---:|---:|---|---:|---:|
| Dev (seuils réglés dessus) | 77 | 0,805 | [0,71 ; 0,88] | 8 / 48 | 1 / 29 |
| Dev, leave-one-out | 77 | 0,740 | [0,65 ; 0,83] | 10 / 48 | 4 / 29 |
| **12 questions neuves** | 12 | **0,917** | [0,75 ; 1,00] | 1 / 10 | **0 / 2** |

« Décision juste » : répondre avec le bon article en tête si la question est dans le Code, s'abstenir sinon. Sur les 12
questions neuves, 9 réponses données, 9 avec le bon article. Sur le dev, 6 des 8 fausses abstentions sont des questions en
tunisien latinisé (refusées par construction) et 2 des traductions arabes ; **aucune question française**. L'AUROC du signal
pour séparer « dans le Code » de « hors Code » est de 0,82 en français et 0,87 en arabe. Sur la **courbe risque-couverture**
(le risque compte les réponses fausses et les réponses hors Code), en ne répondant qu'au quart des questions au signal le
plus élevé le risque est de 5 % ; à la moitié, 24 % ; en répondant à tout, 56 %. Le signal est informatif, mais à couverture
élevée il laisse passer beaucoup d'erreurs : **un seuil seul ne suffit pas** là où une réponse fausse coûte cher. Limites :
seuils réglés sur un dev consulté, 12 questions neuves seulement, 29 questions hors Code dont 3 en arabe.

## 8. Étude d'utilité **[À COMPLÉTER]**

**Question.** LegalTN aide-t-il des étudiants en droit ou en administration à trouver plus justement et plus sûrement une
règle du Code, par rapport au texte et à la recherche par mot-clé ? **Hypothèses**, fixées à l'avance : H1 exactitude plus
élevée avec LegalTN ; H2 temps plus court ; H3 meilleure reconnaissance des questions hors Code ; H4 (exploratoire)
confiance mieux calibrée.

**Plan (prêt).** Plan croisé : chaque étudiant (cible de 12 à 20) répond à deux séries de 6 questions, l'une avec LegalTN,
l'autre avec le Code en PDF et la recherche par mot-clé ; quatre groupes équilibrent la condition et l'ordre. Les 12
questions sont neuves, 2 sont hors Code. Mesures : exactitude, bon article cité, absence de réponse reconnue, temps,
confiance, questionnaire SUS, préférence. Le consentement est écrit, les données sont pseudonymisées. Outils : page de
passation (parcours simulé vérifié), script d'analyse (différence appariée, intervalle bootstrap, test de permutation ;
testé sur données simulées).

**Résultats : non disponibles. Aucune passation n'a eu lieu.** Cette section doit recevoir
`reports/platinum/etude_utilite/RESULTATS.md` après passation et notation.

## 9. Biais de langue

Sur 21 paires question française / traduction arabe, le français retrouve le bon article en tête dans 100 % des cas et
l'arabe dans 62 % (R@1) ; le bon article est dans les 5 premiers pour 90 % des questions arabes : le défaut est de
**classement**, pas de rappel. Étendre la recherche à l'autre langue (poids 1 dans la fusion) ne corrige pas le biais : l'écart de R@1 tombe de 0,38 à 0,10, mais uniquement parce que le français passe de 1,00 à 0,71 ; l'arabe reste à 0,62. Traduire la question arabe en français (qwen2.5:7b) puis chercher donne un R@1 arabe de 0,71, contre 0,62 sans pivot, mais un R@5 de 0,81 contre 0,91 : le pivot place mieux le bon article en tête, il ne le retrouve pas plus souvent dans les cinq premiers,
Le biais est donc mesuré et partiellement compris, pas corrigé.

## 10. Limites et éthique

- **Références de Claude non relues** : obligations, NER, divergences, paraphrases, traductions, questions tunisiennes,
  jugements de fidélité. Un seul « annotateur » ; aucun kappa entre humains.
- Dev consulté pour régler les seuils ; échantillons petits ; LLM locaux non déterministes ; une seule graine pour
  certaines expériences.
- Étiquettes de domaine tirées de la structure du Code : elles mesurent la place d'un article, pas son sujet.
- Texte arabe : 20 passages corrigés, dont 7 déduits du français à confirmer sur image ; d'autres défauts peuvent subsister.
- Le Code a été modifié depuis cette édition ; **LegalTN n'est pas un conseil juridique** (avertissement affiché).
- Textes publics ; aucune donnée personnelle ; l'étude prévoit consentement, pseudonymisation et retrait libre.
- **Publication** : la licence de l'édition source n'est pas clarifiée ; le dossier prêt à publier ne contient ni le texte
  des articles ni les étiquettes du test.

## 11. Reproductibilité

Environnement : `. .\env_silver.ps1` ; tests : `python -m pytest -q`. Commandes par résultat : alignement
`src.alignement_embeddings.evaluer` ; corrections `src.corpus.corriger_arabe` ; audit `src.audit.audit` ; biais de langue
`src.audit.biais_langue` ; obligations `src.obligation_extraction.appliquer_annotations` puis `evaluer_obligations` ;
références `src.obligation_extraction.references_croisees` ; domaine `src.domaine.evaluer` et `src.domaine.lora` ;
abstention `src.platinum.calibration` ; publication `src.publication.preparer` ; étude `src.etude.analyser` ; tableau de
bord `src.rapports.tableau_de_bord`. Journal détaillé : `experiments.md` ; ce qui reste à faire : `RESTE_A_FAIRE.md`.

## Références

- Antoun, W., Baly, F., Hajj, H. (2020). AraBERT: Transformer-based Model for Arabic Language Understanding.
- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*.
- Conneau, A. et al. (2020). Unsupervised Cross-lingual Representation Learning at Scale (XLM-R). *ACL*.
- Cormack, G., Clarke, C., Buettcher, S. (2009). Reciprocal Rank Fusion outperforms Condorcet and individual rank
  learning methods. *SIGIR*.
- Feng, F. et al. (2022). Language-agnostic BERT Sentence Embedding (LaBSE). *ACL*.
- Hu, E. et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models.
- Martin, L. et al. (2020). CamemBERT: a Tasty French Language Model. *ACL*.
- Wang, L. et al. (2022). Text Embeddings by Weakly-Supervised Contrastive Pre-training (E5).

## Annexe — état des exigences du palier Platinum

| Exigence | État | Ce qui manque |
|---|---|---|
| Corpus aligné publié | **Prêt à publier** (alignement sans texte) | Clarifier la licence ; publier (par l'auteure) ; confirmer 7 corrections sur image |
| Jeu d'obligations publié | **Prêt (dev)** : pré-annoté par Claude | Relecture humaine des 300 lignes ; mesure unique du test, puis publication du test |
| Abstention calibrée | **Faite** (courbe risque-couverture, LOO, 12 questions neuves) | Plus de questions neuves, surtout hors Code et en arabe |
| Étude d'utilité avec étudiants | **Conçue, non réalisée** | Recruter, passer, noter, analyser (section 8) |
| Rapport niveau atelier | **Étoffé** (ce document) | Section 8, relecture, mise en forme, export PDF |
