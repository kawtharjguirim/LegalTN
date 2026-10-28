# Vidéo de secours (2 min) — script de narration

Le GIF `video_secours.gif` fait défiler les 8 diapositives (15 s/chacune).
ffmpeg n'est pas installé sur la machine de préparation : le GIF tient lieu
de vidéo de secours, à remplacer par un MP4 si un encodeur est disponible.
Chaque point correspond à une diapositive.

1. **Présentation (0:00)** — LegalTN aligne et interroge le Code du
   travail tunisien bilingue. Quatre composants : alignement AR/FR,
   obligations par règles, NER par CRF, retrieval BM25 avec citation.
2. **Données (0:15)** — 515 articles arabes, 498 français, jeux de
   développement séparés d'un test gelé vérifié par empreintes.
3. **Alignement (0:30)** — appariement par numérotation : 494 couples,
   reproductible octet par octet ; la précision/rappel sur référence
   indépendante attend le lot d'annotation.
4. **Retrieval (0:45)** — sur le dev : rappel@5 de 85 % sans seuil ; le
   seuil historique refuse 27 questions hors périmètre sur 29 au prix de
   4 fausses abstentions, dont le cas « CDI » documenté.
5. **Obligations (1:00)** — extracteur à règles opérationnel sur les 200
   candidats dev ; les scores attendent l'annotation humaine, jamais
   simulée.
6. **NER/CoNLL (1:15)** — le CRF atteint F1=78,9 sur l'espagnol de
   CoNLL-2002 et la baseline publiée est reproduite à 0,09 point près.
7. **Erreurs (1:30)** — 4 catégories d'erreurs réelles sur le dev, aucune
   fabriquée ; 30 erreurs minimum couvertes par le CSV des erreurs.
8. **Limites (1:45)** — tests logiciels complets au vert ; validations
   scientifiques restantes listées ; kappa impossible avec un seul
   annotateur.
