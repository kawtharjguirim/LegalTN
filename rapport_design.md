# Rapport — design final de l'interface LegalTN

Branche `design-final`, créée depuis `design-et-demo` le 9 novembre 2026. Ni push ni tag.
Détail de l'analyse et de la grille : [`design_decision.md`](design_decision.md).

## 1. Les trois directions

Les maquettes statiques sont dans `static/maquettes/`. Elles utilisent le même contenu : deux réponses **réelles** de l'API, enregistrées dans `donnees_exemple.js`. Ajouter `?lang=ar` à l'adresse affiche la version arabe.

| Direction | Idée | Point fort pour ce contexte | Point faible |
|---|---|---|---|
| **A. Institutionnel juridique** (`a_institutionnel.html`) | Papier ivoire, bandeau marine, filet bordeaux, titres serif, fiches d'article | Citation (article, source, page) visible sans clic ; arabe très lisible | Un peu austère |
| B. Moteur de recherche épuré (`b_moteur_epure.html`) | Blanc, une colonne, liste sans cartes | Familier, le moins cher à faire | Générique ; page et étapes au second plan |
| C. Outil d'analyse (`c_outil_analyse.html`) | Résultats et panneau technique permanent (frise, scores, seuil) | Traçabilité maximale | Interface d'ingénieur ; score brut montré à tous ; coût élevé |

Captures des maquettes en FR et en AR : `docs/design/maquettes/<maquette>_fr.png` et `_ar.png`.

## 2. Choix : A, « Institutionnel juridique » (27/30, contre 23 pour B et 19 pour C)

Justification :

- C'est la seule direction où chaque résultat se lit comme une **citation** : article, source, page.
- Son ton officiel convient à un outil qui cite la loi ou s'abstient.
- L'arabe y est le plus lisible : naskh Sakkal Majalla en grand corps.
- Le mode debug est complet (tableau des 8 étapes, langue, latence, corrections, synonymes) sans gêner l'usager.

## 3. Implémentation (`static/index.html`, `app.css`, `app.js`)

- **Structure** : la barre latérale sombre est remplacée par un bandeau marine avec onglets (Accueil, Recherche, À propos). L'état du corpus (496 / 491, en ligne) passe dans le pied de page.
- **Résultats** :
  - fiche à filet bordeaux ;
  - en tête : « Article 14 bis », puis « Code du travail, édition bilingue IORT · page 279 » ;
  - pertinence en barre et en libellé ;
  - texte FR en serif, texte AR en naskh.
- **Mode debug** : annexe « Voir les étapes » en tableau. Ajouts :
  - le **temps de réponse** ;
  - les sorties arabes du pipeline dans une police arabe, alors que l'interface précédente les affichait en monospace, ce qui cassait les liaisons entre les lettres ;
  - le score BM25 brut affiché seulement en mode debug, comme avant.
- **Abstention** : encadré ocre avec un titre. C'est un état normal, pas une erreur.
- **Bandeau de correction** : point d'interrogation arabe « ؟ » en interface arabe, au lieu de « ? ».
- **Accessibilité** :
  - lien d'évitement « Aller à la recherche » ;
  - focus clavier visible (contour bleu de 3 px) ;
  - `aria-pressed` sur les boutons de langue et `aria-current` sur l'onglet actif ;
  - `aria-live` sur les résultats ;
  - textes ≥ 16 px pour le texte courant ;
  - animations coupées si le système demande moins de mouvement.
- **Hors ligne** : aucune ressource externe, uniquement des polices système Windows et des SVG inline.
- **Textes d'accueil** : le ton marketing est retiré (« copilote », « assistant intelligent »). Le texte d'exemple du champ de recherche est remplacé par une question vérifiée.
- **Non modifiés** : l'API, le pipeline, les appels `fetch`, le format des réponses, les questions d'exemple, la case debug mémorisée.

### Fonctions conservées, vérifiées sur les captures

L'état est relevé automatiquement dans `docs/design/apres/audit.json`.

| Fonction | FR | AR |
|---|---|---|
| Bandeau « Vouliez-vous dire » | oui | oui (« هل تقصد: … ؟ ») |
| Surlignage | 46 mots | 49 mots |
| Extrait court / article complet | oui | oui |
| Version alignée | oui (AR sous FR) | oui (FR sous AR) |
| Latence | oui | oui |
| Barre de pertinence et score brut en debug | oui | oui |
| Étapes du pipeline | oui | oui |
| Abstention | oui | oui |
| Mobile 390 px sans défilement horizontal | oui | oui |
| Navigation au clavier (9 × Tab → « Voir la version arabe », focus visible) | oui | non testé |

## 4. Contrastes (WCAG AA)

L'audit est automatique et porte sur tous les textes visibles. Le fond effectif de chaque texte est recalculé, avec un seuil de 4,5:1, ou de 3:1 pour le grand texte. Script : `docs/design/outils/capturer.mjs`.

| Écran | Avant : textes sous AA | Après |
|---|---|---|
| Accueil FR | 2 | 0 |
| Recherche FR (debug) | 9 | 0 |
| Recherche AR (debug) | 9 | 0 |
| Abstention FR | 3 | 0 |
| Mobile FR / AR | 9 / 4 | 0 / 0 |

Les échecs d'avant étaient :

- score brut à 2,58:1 ;
- latence à 2,32:1 et 4,14:1 ;
- pied de la barre latérale à 4,13:1 ;
- bouton de langue inactif à 4,14:1.

L'audit ne couvre **pas** le texte d'exemple du champ de recherche : il est vérifié à la main (`#636B78` sur blanc, 5,4:1). Il ne couvre pas non plus les contours d'éléments non textuels.

## 5. Captures avant / après

| Écran | Avant | Après |
|---|---|---|
| Accueil FR | `docs/design/avant/accueil_fr.png` | `docs/design/apres/accueil_fr.png` |
| Accueil AR | — | `docs/design/apres/accueil_ar.png` |
| Recherche FR, debug, article complet et version arabe | `docs/design/avant/fr_bureau_debug.png` | `docs/design/apres/fr_bureau_debug.png` |
| Recherche AR, debug, article complet et version française | `docs/design/avant/ar_bureau_debug.png` | `docs/design/apres/ar_bureau_debug.png` |
| Abstention FR | `docs/design/avant/fr_abstention.png` | `docs/design/apres/fr_abstention.png` |
| Abstention AR | — | `docs/design/apres/ar_abstention.png` |
| Mobile FR (390 px) | `docs/design/avant/fr_mobile.png` | `docs/design/apres/fr_mobile.png` |
| Mobile AR (390 px) | `docs/design/avant/ar_mobile.png` | `docs/design/apres/ar_mobile.png` |
| Clavier (focus visible) | — | `docs/design/apres/fr_clavier.png` |

Les captures sont faites avec Edge en mode headless, piloté par le protocole DevTools : `docs/design/outils/`. La question est tapée dans le champ, puis le formulaire est envoyé.

## 6. Problèmes rencontrés

- **Capture décalée en arabe.** Une page arabe plus courte que l'écran, capturée en « pleine page », apparaissait décalée de 144 px. La mesure dans le navigateur montre une mise en page correcte : bandeau de 0 à 1280 px, aucun débordement. C'est donc un défaut de la capture. Corrigé en n'utilisant la pleine page que si la page dépasse l'écran.
- **Défauts trouvés sur mes propres captures et corrigés** : « نقاط BM25 » en monospace (lettres détachées), et une barre de défilement parasite dans les onglets en arabe.
- **Message du premier commit.** Celui de `59b93d3` parle de captures « avant/après », mais les captures « après » sont dans le commit d'implémentation. Je n'ai pas réécrit l'historique.
- **Fins de ligne.** Les fichiers `static/` sont stockés en CRLF ; je les ai gardés en CRLF. Les maquettes sont en LF.

## 7. À vérifier par toi

1. **Lance `.\demarrer.ps1 -Port 18765`.** Le port 8000 est occupé par ResearchMind sur ta machine. Essaie :
   - les exemples ;
   - « Mode debug » ;
   - le passage en العربية ;
   - la touche Tab.
2. **Fais relire par un arabophone** les nouveaux textes arabes, que j'ai écrits moi-même :
   - « ابحث عن فصل مجلة الشغل الذي يجيب عن سؤالك » et le paragraphe d'accueil ;
   - « مجلة الشغل، النسخة الثنائية للمطبعة الرسمية » (citation de la source) ;
   - « الانتقال إلى البحث », « زمن الاستجابة », « أمثلة: », « بحث ».
3. **Citation « édition bilingue IORT »** : vérifie que c'est le bon nom de l'éditeur. C'est aussi un point « À VÉRIFIER » de `data_card.md`.
4. **Libellés des articles venant des données**, que je n'ai pas modifiés :
   - en arabe, le badge affiche « الفصل 14 bis » au lieu de « 14 مكرر » ;
   - le résultat « Article 6 » montre le texte « Article 6-2 » (identifiant FR non unique, déjà noté dans le rapport précédent).

   Ils sont bien visibles avec ce design ; à corriger dans le pipeline si tu le souhaites.
5. **Mobile** : le 3ᵉ onglet (« À propos du corpus ») déborde à 390 px. On l'atteint en faisant défiler la barre d'onglets.
6. **Polices** : Sitka et Sakkal Majalla sont des polices de Windows. Sur un autre système, ce sont Georgia, Traditional Arabic, puis la police générique qui prennent le relais. Teste sur la machine de la soutenance.
7. **Fusion de `design-final`** dans `design-et-demo` ou `main` : à faire après ta relecture.

## 8. Fin de session

- pytest : **79 réussis, 1 xfail, 0 échec**.
- Le serveur de démo (port 18765) et Edge headless sont arrêtés à la fin de la session.
- Le serveur ResearchMind (port 8000), qui ne fait pas partie de LegalTN, n'a pas été touché.
