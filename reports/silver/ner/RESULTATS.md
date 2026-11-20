# NER fine-tuné FR / AR — palier Silver (15 novembre 2026)

Commande : `python -X utf8 -m src.ner_juridique.entrainer --langue fr|ar --modeles regles crf <encodeurs>`
(RTX 2050, 4 Go, fp16). Détails par graine et par type : `ner_fr_dev.json`, `ner_ar_dev.json`.

## ⚠️ Nature de la mesure

Les lots dev corrigés à la main (`data/a_annoter/ner_dev_*_v1.csv`) n'ont encore aucune ligne
`verifie`. Les chiffres ci-dessous mesurent donc **l'accord avec les règles** sur une validation
silver (10 % des articles, tirée par graine), **pas la qualité réelle**. Les règles y valent 1,000
par construction. Ils montrent que l'entraînement fonctionne, ce que chaque modèle apprend des
règles, et la stabilité entre graines. Le F1 sur gold sera calculé sans réentraîner dès que les lots
dev seront vérifiés.

## Protocole

- Schéma : ROLE, INSTITUTION, DELAI, MONTANT ; F1 par span exact (caractères), micro et macro.
- Entraînement : corpus silver (règles) — 790 phrases FR, 970 AR — sans les articles des lots
  d'évaluation de la même langue ; validation par article pour l'arrêt précoce.
- Encodeurs : CamemBERT-base (FR), AraBERT v2 base (AR), XLM-R base (FR et AR).
  AdamW, lr 5e-5, lots de 8, 12 époques, warm-up 10 %, meilleur état sur la validation.
  **Embeddings de mots gelés** pour tous les encodeurs (voir « Incidents »).
- Baselines : règles ; CRF du Bronze (traits orthographiques, `src/ner_crf`).
- 3 graines (13, 42, 2026) ; la graine fixe aussi le découpage de validation : l'écart-type
  mélange variance d'initialisation et variance d'échantillon.

## Résultats (accord avec les règles, moyenne ± écart-type sur 3 graines)

| Langue | Système | F1 micro | F1 macro | ROLE | INSTITUTION | DELAI | MONTANT | Durée / graine |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| FR | CRF (Bronze) | 0,838 ± 0,043 | 0,786 | 0,866 | 0,865 | 0,686 | 0,728 | 3 s |
| FR | CamemBERT | 0,798 ± 0,086 | 0,709 | 0,905 | 0,772 | 0,696 | 0,465 | 229 s |
| FR | **XLM-R** | **0,886 ± 0,028** | **0,856** | 0,915 | 0,845 | 0,842 | 0,824 | 254 s |
| AR | CRF (Bronze) | 0,729 ± 0,048 | 0,699 | 0,731 | 0,819 | 0,579 | 0,667 | 3 s |
| AR | **AraBERT v2** | **0,761 ± 0,038** | **0,800** | 0,733 | 0,763 | 0,815 | 0,889 | 346 s |
| AR | XLM-R | 0,687 ± 0,041 | 0,779 | 0,659 | 0,638 | 0,818 | 1,000 | 238 s |

Graine par graine (F1 micro) : CamemBERT 0,846 / 0,699 / 0,848 ; XLM-R FR 0,903 / 0,854 / 0,900 ;
AraBERT 0,720 / 0,795 / 0,768 ; XLM-R AR 0,670 / 0,734 / 0,656.

## Lecture

1. **Français : XLM-R est le meilleur et le plus stable** (± 0,028), devant le CRF et CamemBERT.
   CamemBERT est instable (0,699 sur la graine 42) et faible sur MONTANT (0,465).
2. **Arabe : le modèle monolingue AraBERT l'emporte** sur XLM-R (0,761 contre 0,687) et sur le CRF.
   Le classement s'inverse entre les langues : c'est un résultat à discuter en revue
   (pré-entraînement arabe plus riche d'AraBERT, vocabulaire XLM-R partagé entre 100 langues).
3. **L'arabe est plus difficile pour tous les systèmes** (meilleur micro 0,761 contre 0,886), en
   lien avec la question de recherche du cahier des charges sur la segmentation des clitiques.
4. Les entités gold restent représentables par les tokens (97,5 à 100 % des bornes alignées) :
   la tokenisation n'est pas le facteur limitant.
5. Les encodeurs dépassent les règles qui les ont entraînés seulement si le gold le confirme :
   à mesurer sur les lots corrigés.

## Évaluation sur pré-gold Claude (20 novembre) — lots dev FR et AR

**Nature de la référence** : les 120 phrases dev (60 FR, 60 AR) ont été annotées **par Claude** à
la demande de l'auteure, selon le guide (`data/a_annoter/annotations_claude_dev_v1.json`, décisions
d'annotation incluses), statut `verifie_claude`. C'est un **pré-gold** : il corrige les erreurs
systématiques des règles, mais **ce n'est pas un gold humain indépendant**. Chaque phrase relue
dans `outils/annotateur_ner.html` passe en `verifie`. Commande :
`python -m src.ner_juridique.evaluer_gold --langue fr|ar --accepter-claude` (sans réentraînement :
règles, CRF sur 3 graines, modèles fine-tunés sauvegardés de la graine 13).

| Langue | Système | P | R | **F1 strict** | F1 macro | F1 souple |
|---|---|---:|---:|---:|---:|---:|
| FR (86 entités) | Règles | 0,536 | 0,349 | 0,423 | 0,268 | 0,620 |
| FR | CRF (3 graines : 0,406 / 0,394 / 0,394) | 0,538 | 0,326 | 0,406 | 0,274 | 0,580 |
| FR | **XLM-R** (graine 13) | 0,583 | 0,407 | **0,479** | 0,321 | **0,644** |
| AR (160 entités) | **Règles** | 0,663 | 0,381 | **0,484** | 0,409 | **0,603** |
| AR | CRF (3 graines : 0,364 / 0,379 / 0,366) | 0,631 | 0,256 | 0,364 | 0,280 | 0,462 |
| AR | AraBERT v2 (graine 13) | 0,578 | 0,325 | 0,416 | 0,330 | 0,568 |

F1 strict : bornes et type exacts (mesure principale). F1 souple : chevauchement avec le bon type
(chaque entité appariée une fois). Erreurs catégorisées : `erreurs_pregold_dev_{fr,ar}.csv`.

**Lecture**

1. **L'accord avec les règles surestimait fortement la qualité** (XLM-R FR 0,886 → 0,479 strict).
   Entraînés sur des annotations par règles, les modèles héritent de leurs oublis : le **rappel**
   (0,26 à 0,41) est le point faible, et l'**oubli** est de loin la première catégorie d'erreur
   (FR : 30 à 37 ; AR : 72 à 97).
2. **En français, le fine-tuning généralise au-delà des règles** : XLM-R les dépasse en strict
   (+5,6 points) comme en souple (+2,4 points), surtout sur ROLE et INSTITUTION.
3. **En arabe, non** : les règles restent devant AraBERT (0,484 contre 0,416), et le CRF est le plus
   faible. Le corpus silver arabe, plus bruité (OCR), transmet moins bien la supervision.
4. **DELAI à 0 en strict en français** : désaccord de **frontières**, pas d'oubli — la référence
   prend l'expression entière (« dans un délai n'excédant pas trois jours », « 1 à 15 jours »),
   les règles seulement « trois jours ». D'où l'intérêt du F1 souple.
5. Suite logique : réentraîner sur un silver amélioré (règles corrigées des erreurs révélées ici :
   âges en MONTANT, délais en heures, « رئيس » + organisme = ROLE, variante « تفقديّة ») ou ajouter
   le pré-gold à l'entraînement — en gardant alors un lot test séparé.

## Correctif postérieur aux mesures (16 novembre)

Le décodage des prédictions (`spans_depuis_tokens`) découpait en deux une entité quand le
tokenizer de XLM-R produit des offsets chevauchants (« ▁ » puis « vingt » sur la même position) :
`[v]MONTANT[vingt-quatre heures]MONTANT`. Corrigé et testé ; les F1 de XLM-R ci-dessus ont été
calculés **avant** ce correctif et sont donc possiblement un peu sous-estimés. Tout sera
recalculé lors de l'évaluation sur gold.

Modèles de démonstration (graine 13, embeddings gelés) : `models/ner/fr_xlmr` (accord 0,909) et
`models/ner/ar_arabert` (0,732), utilisés par `python -m src.ner_juridique.predire "phrase"`.

## Incidents et choix

- **Premier essai : F1 = 0,000** (CamemBERT, lr 3e-5, lots de 16, 6 époques) : le modèle ne
  prédisait que « O » (entités rares). Avec lr 5e-5, lots de 8, le F1 de validation monte de 0 à
  0,78 en 8 époques ; 12 époques retenues. Réglage fait sur la validation silver, jamais sur gold.
- **XLM-R débordait de la VRAM** (3 955 / 4 096 Mo, 38 min par graine au lieu de 4) : sa matrice
  d'embeddings (250 k × 768 = 192 M paramètres) et ses états AdamW passaient en mémoire partagée.
  Gel des embeddings de mots pour **tous** les encodeurs (comparaison équitable) : 3,2 Go,
  ≈ 4 min par graine ; CamemBERT 0,846 (gelé) contre 0,833 (non gelé) sur la graine 13.
