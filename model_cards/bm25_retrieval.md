# Carte de modèle — Recherche BM25 avec abstention — BROUILLON « À VÉRIFIER »

> Brouillon préparé par l'assistant (9 novembre 2026). Chiffres repris de `experiments.md`.

| Élément | Valeur |
|---|---|
| Code | `src/evaluation/baseline_bm25.py` (index), `src/demo/repondre.py` (démo historique), `src/pipeline/traitement.py` (pipeline complet) |
| Type | modèle lexical BM25, sans apprentissage ; aucun LLM ni réseau neuronal |
| Paramètres | k1 = 1,5 ; b = 0,75 (valeurs standard, non réglées) |
| Abstention | score du meilleur article < **9,085** (choisi sur `questions_dev_v1`, inchangé depuis) |
| Entrée | question FR, AR, tunisien ou arabizi |
| Sortie | jusqu'à 5 articles (numéro, page, extrait), ou abstention |

## Résultats (dev v2, non indépendant)

| Système | R@1 | R@5 | Abstentions à tort | Refus hors périmètre |
|---|---|---|---|---|
| aléatoire (baseline triviale) | 0/27 | 0/27 | 0/27 | 0/29 |
| mots communs (baseline triviale) | 13/27 | 23/27 | 0/27 | 0/29 |
| BM25 historique, seuil 9,085 | 21/27 | 21/27 | 4/27 | 27/29 |
| pipeline complet, seuil 9,085 | 20/27 | 22/27 | 0/27 | 23/29 |

**Aucun résultat sur test gelé** à ce jour — **À FAIRE** une seule fois, sur le pipeline final.

## Limites

- Correspondance lexicale : « hebdomadaire » ne retrouve pas « par semaine » sans synonyme.
- Le seuil 9,085 a été fixé pour le BM25 historique ; il n'est plus adapté aux scores du
  pipeline complet (scores FR+AR additionnés pour l'arabizi) — réglage unique prévu.
- Questions tunisiennes et arabizi mal couvertes (R@5 2/6).

## Usage prévu

Démonstration académique : citer l'article pertinent du Code du travail. **Ne remplace pas
un avis juridique.** — **À VÉRIFIER** : formulation de l'avertissement par l'équipe.
