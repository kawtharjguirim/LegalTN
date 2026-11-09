# Carte de modèle — NER par CRF — BROUILLON « À VÉRIFIER »

> Brouillon préparé par l'assistant (9 novembre 2026). Chiffres repris de
> `reports/reprise/conll2002_reproduction.json`, re-vérifiés lors de l'audit du 9 novembre.

| Élément | Valeur |
|---|---|
| Code | `src/ner_crf/features.py`, `pipeline.py`, `reproduire_baseline_conll.py` |
| Type | champ aléatoire conditionnel linéaire (sklearn-crfsuite 0.5.0), pas de réseau neuronal |
| Paramètres | algorithme L-BFGS, c1 = 0,1, c2 = 0,1, 100 itérations |
| Traits | orthographiques (casse, suffixes, chiffres…) et contexte ± 2 mots, sans liste externe |
| Données d'entraînement | CoNLL-2002 espagnol (8 323 phrases train, 1 517 test), via NLTK |

## Résultats

| Mesure (CoNLL-2002 espagnol, test) | Valeur |
|---|---|
| F1 micro par span | 78,90 (PER 87,27 ; ORG 79,20 ; LOC 78,41 ; MISC 57,92) |
| Baseline publiée reproduite (Tjong Kim Sang, 2002) | 35,95 obtenu contre 35,86 publié (+0,09) |

## Limites — IMPORTANT

- **Le CRF n'est pas encore entraîné sur le corpus juridique** : 0/60 phrase annotée dans
  `data/dev/ner_a_annoter_v1.csv`. Les types prévus (ROLE, INSTITUTION, DELAI, MONTANT)
  ne sont pas ceux de CoNLL (PER, ORG, LOC, MISC).
- Les chiffres ci-dessus valident l'implémentation, pas un NER LegalTN.
- **À FAIRE** : annoter (60 minimum, 200 conseillé), entraîner, mesurer le F1 par span ;
  accord inter-annotateurs avec `calculer_kappa.py --mode spans`.
