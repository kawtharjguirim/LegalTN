# Guide — validation des questions candidates (Gold)

`questions_candidates_ia.csv` contient 50 questions **proposées par une IA (Claude)** : 15 en tunisien, 10 en arabizi, 15 en arabe standard, 10 hors périmètre. Elles n'ont **aucun article de référence** : c'est toi qui décides.

Pour chaque ligne :

1. **question_naturelle** : `oui` si un vrai Tunisien poserait la question comme ça ; `non` sinon.
2. **question_corrigee** : si `non`, réécris-la comme tu la dirais (sinon laisse vide).
3. **article_attendu** : cherche dans le PDF du Code du travail l'article qui répond (ex. `79`, `14 bis`). Si plusieurs, sépare par `;`. Si tu ne trouves pas, laisse vide et mets un commentaire.
4. **hors_perimetre** : `oui` si le Code du travail ne répond pas à la question (même si le type proposé dit autre chose).
5. **commentaire** : tout doute.

Règles :
- Ne te fie pas au « type_propose » : vérifie toi-même.
- Supprime (ou marque `non` sans correction) une question absurde.
- Plusieurs questions reprennent des sujets du dev français (traductions) : elles serviront aussi à mesurer l'écart FR / AR sur le même sujet.

Dans le rapport, ces questions seront présentées comme « générées par IA, validées et étiquetées par un humain », séparément des questions écrites à la main.
