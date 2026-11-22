# Brouillon — Section Limitations chiffrée (à compléter après les mesures Gold)

1. **Taille et indépendance des jeux** : 54 questions de dev (26 dans le périmètre), déjà utilisées pour concevoir les prompts ; une question = 3,8 points. Mesure unique sur test_locked pas encore faite.
2. **Langues** : 0 question arabe dans le périmètre du dev ; 6 en tunisien. Bon article cité P2V : FR 16/20 contre tunisien 2/6. Arabizi en recherche : BM25 R@1 1/6, e5 0/6.
3. **Refus injustifiés** : P2V s'abstient à tort sur 3 à 4 questions sur 26 (12–15 %), selon l'exécution.
4. **Variabilité** : deux exécutions identiques (température 0, graine fixe) diffèrent d'une question sur le refus hors périmètre (26 contre 27/28) et les fausses abstentions (3 contre 4/26).
5. **Fine-tuning** : alignement FR↔AR amélioré (R@1 AR→FR 84 → 87/87) mais recherche question → article dégradée (R@5 22 → 9,33/27).
6. **Réponses très courtes** : le RAG répond souvent par le seul numéro d'article (ex. « Article 140 »), ce qui ne répond pas à la question pour un usager.
7. **LLM-juge non validé** : même modèle que le RAG (3B) ; sur 23 réponses jugées, 6 erreurs serveur et 2/17 jugées fidèles, ce qui paraît trop sévère. Validation humaine (kappa) à faire avant tout usage.
8. **Divergences AR / FR** : le détecteur par règles signale 227 articles sur 436, signal très bruité (artefacts d'extraction PDF dans les nombres) ; précision à mesurer sur 60 articles annotés.
9. **Information, pas conseil** : le système ne remplace pas un juriste ; corpus limité au Code du travail.
