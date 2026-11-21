# Classification de domaine des articles — résultats (21 novembre 2026)

Commandes :
```
python -X utf8 -m src.domaine.etiquettes     # étiquettes et contrôle des bornes
python -X utf8 -m src.domaine.evaluer        # TF-IDF, e5, bilingue, transfert (3 graines)
python -X utf8 -m src.domaine.lora           # LoRA sur e5 (GPU, 1 graine)
```
Code : `src/domaine/` ; tests : `tests/test_domaine.py` ; détail : `resultats.json`, `lora.json`,
`erreurs_e5_fr.csv`.

## Tâche et étiquettes

Prédire le **domaine** d'un article (12 classes) d'après son seul texte, en français et en arabe.
Les étiquettes ne sont **ni annotées à la main ni produites par un modèle** : elles viennent de la
**structure du Code** (livres, titres, chapitres). Le texte français place l'intitulé du chapitre suivant à
la fin de l'article qui précède (« … Chapitre III Fin du contrat de travail » clôt l'article 13) ; ces
intitulés donnent les bornes des 18 plages d'articles regroupées en 12 domaines.

| Domaine | Articles FR | Articles AR |
|---|---:|---:|
| conflits et juridictions | 73 | 73 |
| durée, repos, congés | 66 | 65 |
| contrat de travail | 54 | 51 |
| emploi et formation | 54 | 50 |
| hygiène, sécurité, santé | 49 | 46 |
| statuts particuliers | 47 | 47 |
| conditions et protection du travail | 39 | 37 |
| inspection et sanctions | 24 | 24 |
| conventions collectives | 20 | 20 |
| salaire | 19 | 19 |
| représentation du personnel | 17 | 16 |
| syndicats | 16 | 15 |

478 articles français et 463 arabes (articles abrogés exclus).

**Solidité des bornes** (`verifier_bornes`) : sur les 17 frontières entre plages, **17 sont confirmées par
un intitulé de structure français** en fin d'article précédent et **15 par un changement de chapitre dans la
hiérarchie arabe** (`articles_ar.csv`, colonne `chapitre`) ; la hiérarchie arabe est fausse à 2 endroits
(372–390 et 409–444, où des intitulés manquent). **Le regroupement des chapitres en 12 domaines est une
décision de conception** (par exemple « statuts particuliers » réunit journalistes, voyageurs de commerce,
boulangers, médaille du travail) : il n'est pas validé par un juriste.

**Prévention des fuites.** Le texte est nettoyé : intitulé numéroté de l'article supprimé, intitulé de
structure final supprimé (il nomme le chapitre suivant, donc l'étiquette), numéros d'articles cités remplacés
par « N » (les articles voisins partagent leur domaine).

## Protocole

Validation croisée **par blocs** : 5 plis, blocs de 6 numéros d'articles consécutifs jamais séparés entre
apprentissage et test (un découpage aléatoire gonflerait les scores, les voisins se ressemblent) ; un article
français et son équivalent arabe tombent dans le même pli. 3 graines (la graine change l'affectation des
blocs aux plis). Macro-F1 sur les prédictions des 5 plis, moyenne ± écart-type sur les graines. Régression
logistique à classes équilibrées.

## Résultats (macro-F1)

| Système | Macro-F1 | Exactitude |
|---|---:|---:|
| Majorité (FR) | 0,019 ± 0,004 | 0,071 |
| TF-IDF + LR, français (mots 1–2) | 0,575 ± 0,018 | 0,602 |
| TF-IDF + LR, arabe (caractères 2–5) | 0,607 ± 0,018 | 0,641 |
| **e5 + LR, français** | **0,631 ± 0,024** | 0,658 |
| e5 + LR, arabe | 0,600 ± 0,033 | 0,622 |
| e5 + LR bilingue, test français | 0,613 ± 0,034 | 0,646 |
| e5 + LR bilingue, test arabe | 0,566 ± 0,040 | 0,598 |
| **Transfert** : appris en français, testé en arabe | 0,409 ± 0,020 | 0,463 |
| **Transfert** : appris en arabe, testé en français | 0,412 ± 0,026 | 0,502 |

### Fine-tuning LoRA (multilingual-e5-base, rang 8, projections query et value)

Même protocole (5 plis par blocs), **une seule graine** (graine 0, 8 époques, ~10 minutes pour les 10
modèles sur la carte de 4 Go). Comparaison avec les autres systèmes **sur la même graine 0** :

| Système | LoRA | e5 + LR (graine 0) | Écart |
|---|---:|---:|---:|
| Français → français | **0,713** | 0,617 | +0,096 |
| Arabe → arabe | **0,638** | 0,580 | +0,058 |
| Transfert français → arabe | 0,453 | 0,400 | +0,053 |
| Transfert arabe → français | 0,518 | 0,392 | +0,126 |

Exactitude : 0,734 (FR), 0,650 (AR), 0,492 (FR→AR), 0,590 (AR→FR).

## Lecture

1. **La tâche est faisable mais pas facile** : ~0,6 de macro-F1 pour 12 domaines contre 0,02 pour la
   majorité. Les embeddings e5 battent TF-IDF en français (+0,056, soit environ 2 écarts-types) mais pas en
   arabe (0,600 contre 0,607, indiscernable).
2. **Le transfert entre langues fonctionne partiellement** (0,41, vingt fois le hasard) mais perd un tiers
   par rapport à l'apprentissage dans la langue : un classifieur appris en français sert en arabe sans
   étiquette arabe, avec une qualité nettement moindre. **Ajouter l'autre langue à l'apprentissage
   n'aide pas** (bilingue ≤ monolingue).
3. **LoRA fait mieux que la régression logistique sur les embeddings figés** dans les quatre cas (+0,05 à
   +0,13 de macro-F1 sur la même graine), y compris en transfert : adapter les couches de l'encodeur aide,
   en français (0,71) comme en arabe (0,64). Le meilleur transfert reste inférieur à l'apprentissage dans la
   langue (0,52 contre 0,71 en test français). **Réserve** : une seule graine pour LoRA ; l'écart de 0,05 à 0,10
   dépasse la dispersion observée entre graines des autres systèmes (0,05 pour e5 + LR en français), mais
   l'écart-type de LoRA n'est pas mesuré.
4. **Domaines faciles** (F1 e5 français) : conflits et juridictions 0,86, durée-repos-congés 0,81, syndicats
   0,80, conditions et protection 0,75, conventions collectives 0,73. **Difficiles** : salaire 0,41,
   inspection et sanctions 0,41, contrat de travail 0,52, hygiène-sécurité 0,55, statuts particuliers 0,55.
   Les confusions principales : statuts particuliers → contrat de travail (9 articles), hygiène-sécurité →
   inspection et sanctions (9), emploi et formation → inspection et sanctions (8). Les domaines
   « inspection et sanctions » et « statuts particuliers » sont définis par la **place** dans le Code plus
   que par le sujet : les articles de sanctions parlent de congés, de salaires, de sécurité.

## Limites

- Étiquettes issues de la structure du Code : un article classé dans un chapitre peut traiter d'un autre
  sujet (articles de sanctions, dispositions générales) ; la « vérité » mesurée est la place dans le Code,
  pas le sujet vu par un juriste. Aucune relecture humaine.
- Regroupement en 12 domaines non validé ; changer le regroupement change les scores.
- Petits effectifs (16 à 73 articles par domaine) ; un article = un exemple, texte tronqué à 256 jetons.
- Les écarts-types sont sur 3 découpages d'un même jeu, pas sur des échantillons indépendants.
- LoRA : une graine, hyperparamètres (rang 8, taux 3e-4, 8 époques) non réglés ; aucun réglage sur les plis
  de test, mais aucune validation séparée non plus. Le F1 par domaine de LoRA n'est pas détaillé.
- Les mentions de lois modificatives (« Modifié par la loi n° … ») ne sont pas supprimées en arabe quand
  l'intitulé est mal formé (15 articles) : légère fuite de période, sans lien direct avec le domaine.
