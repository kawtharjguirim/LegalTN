# Choix du design de l'interface LegalTN

Branche `design-final`. Maquettes : `static/maquettes/`. Captures : `docs/design/`.

## 1. Analyse du contexte

| Contrainte | Conséquence pour le design |
|---|---|
| **Usage** : salariés, employeurs, étudiants cherchent un article de loi fiable, pas une conversation | Pas d'interface de chat. Le résultat est une **fiche d'article** : numéro, page, extrait, accès au texte complet. Ton sobre, pas de vocabulaire marketing (« copilote », « intelligent »). |
| **Jury** (module NLP, ESPRIM) : clarté, traçabilité, honnêteté | La provenance se lit sans clic : article, page, source (« Code du travail, édition bilingue IORT »). Les corrections sont visibles (« Vouliez-vous dire »). Les étapes du pipeline sont lisibles en mode debug. L'abstention est un état à part entière, pas une erreur. |
| **Bilinguisme** FR / AR, droite-gauche, arabizi | Mise en page en propriétés logiques (`inline-start`). Une police arabe lisible pour le texte des articles. Chaque texte porte sa propre direction (`dir`), même au milieu de l'autre langue. Les sorties arabes du pipeline ne doivent pas être en police monospace : elle casse les liaisons entre lettres (constaté sur la maquette A). |
| **Démo hors ligne** | Aucun CDN. Polices **système** de Windows (Segoe UI, Sitka, Georgia, Sakkal Majalla, Tahoma), avec des repères génériques en dernier recours. Icônes en SVG inline. Aucune police embarquée : cela évite les licences à vérifier et le poids. |
| **Accessibilité** | Contraste AA (4,5:1 pour le texte normal, 3:1 pour le grand texte). Texte courant ≥ 16 px, arabe plus grand. Focus clavier visible. Boutons de langue avec `aria-pressed`. Lien d'évitement vers la recherche. |
| **Fonctions à conserver** | Toutes sont présentes dans les trois maquettes : bandeau de correction, surlignage, extrait / article complet, version alignée, latence, pertinence, étapes, abstention, responsive. |

**État de départ** (`docs/design/avant/`) : l'audit automatique trouve **2 à 9 textes sous AA** selon l'écran :

- score BM25 brut 2,58:1 ;
- latence 2,32:1 et 4,14:1 ;
- pied de la barre latérale 4,13:1 ;
- bouton de langue inactif 4,14:1.

Le ton est celui d'une application grand public (« copilote », « assistant intelligent »).

## 2. Trois directions

Toutes les maquettes utilisent le même contenu : deux **réponses réelles** de l'API, enregistrées dans `static/maquettes/donnees_exemple.js`.

- FR : « quel est le préavi de rupture d'un contart CDI ? », avec 3 corrections.
- AR : « … عقد الشغلل؟ », avec 1 correction.

Chacune donne 3 résultats et le panneau des étapes. Les maquettes s'ouvrent avec `?lang=ar` pour la version arabe.

### A. Institutionnel juridique — `a_institutionnel.html`

- **Palette** : papier ivoire `#FAF8F3`, encre `#1C2127`, bleu marine `#14365A`, filet bordeaux `#8C1D2C` (rappel du rouge tunisien, assombri pour le contraste).
- **Typographie** :
  - FR : titres en serif (Sitka Heading, Georgia), texte des articles en serif (Sitka Text), interface en Segoe UI ;
  - AR : texte des articles en **Sakkal Majalla**, une naskh à 1,4 rem, et interface en Segoe UI.
- **Mise en page** : bandeau marine, une colonne de 860 px.
- **Résultats** : chaque résultat est une fiche avec un filet bordeaux, « Article 14 bis » en grand, puis la citation de la source et de la page.
- **Mode debug** : une « annexe » repliable, sous forme de tableau étape → sortie.
- **Forces** : évoque le Journal officiel, donc inspire confiance ; la citation est explicite ; l'arabe est très lisible.
- **Faiblesses** : un peu austère ; la serif rend le texte un peu plus long ; l'annexe est loin des résultats si la liste est longue.

### B. Moteur de recherche épuré — `b_moteur_epure.html`

- **Palette** : blanc, texte `#1F2328`, liens bleus `#0B57D0`, source en vert.
- **Typographie** : Segoe UI partout, FR et AR.
- **Mise en page** : une colonne de 760 px, barre de recherche arrondie, liste sans cartes.
- **Mode debug** : étapes en pastilles sous la barre de recherche.
- **Forces** : familier, très clair, implémentation la moins coûteuse.
- **Faiblesses** :
  - ressemble à un moteur web générique, alors que le contenu est juridique ;
  - le numéro d'article ressemble à un lien et la page passe au second plan ;
  - les pastilles d'étapes sont difficiles à lire dès qu'elles s'allongent.

### C. Outil d'analyse avec panneau technique — `c_outil_analyse.html`

- **Palette** : en-tête ardoise `#0F172A`, fond `#F1F5F9`, sarcelle `#0F766E`.
- **Typographie** : Segoe UI, avec Cascadia Mono pour les données.
- **Mise en page** : deux colonnes. Les résultats sont à gauche. Un panneau permanent à droite montre la langue, la latence, les corrections, les 8 étapes en frise, puis les scores BM25 bruts face au seuil 9,085.
- **Forces** : traçabilité maximale ; le jury voit tout d'un coup d'œil.
- **Faiblesses** :
  - interface d'ingénieur, peu adaptée à un salarié ;
  - le score brut est affiché à tous, alors que l'interface actuelle le réserve au mode debug ;
  - le monospace casse l'arabe ;
  - deux colonnes à replier sur mobile, donc le coût le plus élevé.

## 3. Grille et choix

Notes de 1 (faible) à 5 (fort), données par moi d'après les maquettes et les captures.

| Critère | A institutionnel | B épuré | C analyse |
|---|---|---|---|
| Clarté pour un usager | 5 | 5 | 3 |
| Traçabilité pour le jury (article, page, étapes) | 4 | 2 | 5 |
| Lisibilité arabe | 5 | 4 | 3 |
| Sobriété juridique | 5 | 3 | 2 |
| Accessibilité (AA, clavier, tailles) | 4 | 4 | 4 |
| Coût d'implémentation (5 = faible) | 4 | 5 | 2 |
| **Total / 30** | **27** | **23** | **19** |

**Choix : A, « Institutionnel juridique ».**

Justification :

1. C'est la seule direction qui affiche la citation complète (article, source, page) sur chaque résultat sans clic : c'est la traçabilité attendue par le jury et par un usager du droit.
2. Son ton, proche d'une publication officielle, convient à un outil qui cite la loi ou s'abstient, mieux qu'un moteur générique (B) ou un tableau de bord (C).
3. L'arabe y est le plus lisible : naskh Sakkal Majalla en grand corps, direction propre à chaque bloc.
4. Le mode debug reste complet (tableau des étapes) sans encombrer l'usager, qui ne le voit qu'en le cochant.
5. On reprend un point de C : la latence et la langue détectée restent en tête de l'annexe.
6. Coût : CSS et gabarit HTML à refaire, logique JS conservée. L'API et le pipeline ne changent pas.
7. Écart B/C avec A : 4 et 8 points, surtout sur la traçabilité (B) et sur la sobriété et l'arabe (C).
