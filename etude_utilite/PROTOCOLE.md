# Étude d'utilité de LegalTN — protocole (v1, 21 novembre 2026)

**Statut : protocole prêt, aucune passation réalisée.** Tous les résultats futurs de cette étude sont à
produire avec de vrais participants ; rien dans ce dépôt n'est un résultat d'étude.

## 1. Question

LegalTN aide-t-il des étudiants en droit ou en administration à **trouver plus justement et plus
sûrement** une règle du Code du travail, par rapport à leur méthode habituelle (le texte du Code et la
recherche par mot-clé) ?

Hypothèses, fixées avant la passation :
- **H1** : l'exactitude des réponses (bonne règle, bon article cité) est plus élevée avec LegalTN.
- **H2** : le temps par question est plus court avec LegalTN.
- **H3** : sur les questions **hors du Code**, les participants reconnaissent plus souvent
  l'absence de réponse avec LegalTN (abstention).
- **H4** (exploratoire) : la confiance déclarée est mieux calibrée : moins de réponses fausses données
  avec une confiance élevée.

## 2. Plan

**Mesures répétées croisées (« within-subject »)** : chaque participant utilise les deux conditions.

| Condition | Outil |
|---|---|
| **LegalTN** | l'application de démo (`demarrer.ps1`, moteur hybride) : réponse citée + extrait + page |
| **Code seul** (référence) | le PDF bilingue du Code du travail et sa recherche par mot-clé (`Ctrl+F`) |

Deux **ensembles de tâches** équivalents (A et B, 6 questions chacun : 5 dans le Code, 1 hors du Code,
`taches_v1.csv`). Quatre groupes répartissent condition et ordre (affectation par tirage, à équilibrer) :

| Groupe | Bloc 1 | Bloc 2 |
|---|---|---|
| G1 | LegalTN, ensemble A | Code seul, ensemble B |
| G2 | LegalTN, ensemble B | Code seul, ensemble A |
| G3 | Code seul, ensemble A | LegalTN, ensemble B |
| G4 | Code seul, ensemble B | LegalTN, ensemble A |

Cet équilibrage évite que l'effet soit confondu avec la difficulté d'un ensemble ou avec l'ordre.

## 3. Participants

- **Cible : 12 à 20 étudiants** en droit, administration ou gestion (au moins 3 par groupe) ; 16 est un
  bon compromis (4 par groupe). Avec moins de 10, aucune conclusion statistique n'est possible : l'étude
  devient qualitative.
- Critères : avoir suivi un cours de droit ; ne **pas** avoir participé au développement de LegalTN.
- **Consentement** écrit (texte dans la page de passation), participation volontaire, retrait possible à
  tout moment, **données pseudonymisées** (code `P01`…). Aucune donnée personnelle collectée. Si l'étude
  est menée dans un établissement : accord de l'enseignant ou du responsable.

## 4. Passation (30 à 40 minutes par personne)

1. Accueil et consentement (page `outils/etude_utilite.html`) ; profil (domaine, année, familiarité avec
   le Code, usage d'outils d'IA).
2. **Bloc 1** : 6 questions, une à la fois, avec la condition du groupe. Pour chaque question : réponse
   rédigée, article cité, case « je n'ai pas trouvé de réponse dans le Code », confiance (1–5). Le temps
   est mesuré par la page (affichage → validation).
3. Questionnaire d'utilisabilité **SUS** (10 items) + 3 items propres au bloc.
4. **Bloc 2** : mêmes étapes avec l'autre condition.
5. Préférence finale, intention d'usage et commentaire libre.
6. Export des résultats (JSON et deux CSV) ; le facilitateur sauvegarde dans `etude_utilite/resultats/`.

Consignes au facilitateur : ne pas aider à répondre ; ne pas révéler les corrigés ; noter les incidents
(panne d'Ollama, lenteur) ; faire un **essai à blanc** avec une question hors série. Au maximum 8 minutes
par question.

## 5. Notation

Chaque réponse est notée **à l'aveugle de la condition** (le fichier de notation ne contient pas la
condition) par la grille suivante, avec le corrigé de `taches_v1.csv` :

| Note | Définition |
|---|---|
| `note_reponse` = 1 | la réponse contient tous les points clés du corrigé et rien de contraire |
| `note_reponse` = 0 | point clé manquant, faux, ou contraire au Code |
| `note_article` = 1 | l'article cité est celui du corrigé |
| Question hors Code | `note_reponse` = 1 seulement si le participant indique qu'il n'y a pas de réponse dans le Code |

Idéalement **deux notateurs** indépendants sur au moins 30 % des réponses, avec kappa de Cohen
(`src/juge/juge.py : kappa`). Avec un seul notateur, le dire.

## 6. Analyse (script : `python -X utf8 -m src.etude.analyser`)

- Par condition : exactitude, citation correcte, abstention correcte (hors Code), temps (médiane),
  confiance moyenne ; **confiance moyenne sur les réponses fausses** (calibration, H4).
- Comparaison **appariée par participant** : différence moyenne, intervalle de confiance bootstrap à 95 %,
  test de permutation par inversion de signes. Pas de seuil magique : on rapporte l'effet et l'intervalle.
- SUS : score 0–100 par condition (moyenne et différence appariée).
- Préférence : effectifs. Commentaires : lecture et regroupement par thèmes.

## 7. Limites à annoncer

- Petit échantillon, étudiants volontaires (biais de sélection) ; pas de juristes en exercice.
- Questions courtes à réponse précise : l'étude ne mesure pas le raisonnement juridique.
- L'outil est un prototype : lenteur ou panne du LLM local pèsent sur le temps et la satisfaction.
- Un seul notateur par défaut ; le corrigé a été rédigé par l'auteure du projet (et donc par l'équipe
  qui connaît l'outil). Les 12 questions sont nouvelles : aucune ne figure dans les jeux de
  questions de développement ni de test (vérifié sur les articles de référence) ; certains articles (63-2,
  73, 150, 153, 254) apparaissent toutefois dans les phrases des jeux d'obligations, sans effet sur la
  recherche.
- Le texte arabe a des défauts d'OCR : l'étude se fait **en français**.

## 8. Ce qu'il reste à faire pour mener l'étude

1. Recruter les participants et fixer les dates (enseignant, cours de droit du travail).
2. Faire valider les 12 tâches et leur corrigé par un juriste ou un enseignant.
3. Faire un pilote avec 2 personnes, corriger les consignes.
4. Passer l'étude, noter, analyser, puis écrire la section « étude d'utilité » du rapport
   (`reports/platinum/RAPPORT.md`, section 5, qui contient des emplacements à compléter).
