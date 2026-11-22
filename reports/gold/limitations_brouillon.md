# Brouillon — Section Limitations chiffrée (à compléter après les mesures Gold)

1. **Taille et indépendance des jeux** : 54 questions de dev (26 dans le périmètre), déjà utilisées pour concevoir les prompts ; une question = 3,8 points. Mesure unique sur test_locked pas encore faite.
2. **Transfert vers le dialecte** (50 questions Gold) : hybride R@5 arabe 13/15, tunisien 6/13, arabizi 1/9 ; RAG P2V bon article arabe 7/15, tunisien 2/13, arabizi 0/9 (FR dev : 16/20). Le goulot est la recherche.
2b. **Biais entre langues** : sur 3 sujets posés dans les 4 langues, FR et arabe réussissent 3/3, tunisien et arabizi 0/3 ; sur 7 sujets AR/tunisien/arabizi : RAG correct 3, 0, 0. Aucun sujet n'obtient la même réponse dans les 4 langues (INV 0/3).
3. **Refus injustifiés** : P2V s'abstient à tort sur 3 à 4 questions sur 26 (12–15 %), selon l'exécution.
4. **Variabilité** : deux exécutions identiques (température 0, graine fixe) diffèrent d'une question sur le refus hors périmètre (26 contre 27/28) et les fausses abstentions (3 contre 4/26).
5. **Fine-tuning** : alignement FR↔AR amélioré (R@1 AR→FR 84 → 87/87) mais recherche question → article dégradée (R@5 22 → 9,33/27).
6. **Réponses très courtes** : le RAG répond souvent par le seul numéro d'article (ex. « Article 140 »), ce qui ne répond pas à la question pour un usager.
7. **LLM-juge non validé** : même modèle que le RAG (3B) ; sur 23 réponses jugées, 6 erreurs serveur et 2/17 jugées fidèles, ce qui paraît trop sévère. Validation humaine (kappa) à faire avant tout usage.
7b. **Données Gold** : 50 questions proposées par IA puis étiquetées par un seul annotateur (3 corrections après lecture du texte) ; aucun kappa inter-annotateurs.
8. **Divergences AR / FR** : le détecteur par règles signale 227 articles sur 436, signal très bruité (artefacts d'extraction PDF dans les nombres) ; précision à mesurer sur 60 articles annotés.
9. **Information, pas conseil** : le système ne remplace pas un juriste ; corpus limité au Code du travail.
