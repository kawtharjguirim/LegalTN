# Travail manuel à faire par l'équipe

Ces fichiers ne peuvent **pas** être remplis automatiquement : ce sont des données
humaines (annotations, questions de référence, lexiques). Aucun n'a été rempli par
l'assistant. Les exemples ci-dessous sont soit tirés de vos guides et fichiers
existants, soit des **schémas de format** signalés comme tels : ne pas les recopier
comme annotations.

Règles communes :

- remplir le **dev** d'abord ; ne jamais regarder les résultats du **test gelé** pour
  ajuster une règle, un lexique ou un seuil ;
- un champ vide = « pas encore annoté » (jamais « non ») ;
- dès qu'un nouveau jeu de test est terminé : calculer son SHA-256, le consigner dans
  `experiments.md` avec la date, le placer dans `data/test_locked/`, puis le committer.

| # | Fichier | Statut actuel | Lignes conseillées | Bloque |
|---|---|---|---|---|
| 1 | `data/dev/lexique_tunisien_v1.csv` | 5 lignes MODÈLE à valider | 150 à 300 | étape 5 du pipeline (tunisien, arabizi) |
| 2 | `data/dev/synonymes_juridiques_v1.csv` | 5 lignes MODÈLE à valider | 50 à 100 paires | étape 8 du pipeline |
| 3 | `data/dev/questions_dev_v3_multilingue.csv` (à créer) | absent | 60 dev + 60 test | rappel AR / tunisien / arabizi |
| 4 | `data/dev/questions_fautes_manuelles_v1.csv` (à créer) | absent | 56 (une par question du dev v2) | mesure SymSpell sur vraies fautes |
| 5 | `data/dev/obligations_candidats_dev_v1.csv` (+ test gelé) | 0/200 dev, 0/100 test | 200 + 100 | F1 par rôle des obligations |
| 6 | `data/dev/ner_a_annoter_v1.csv` | 0/60 | 60 minimum, 200 conseillé | F1 NER par span |
| 7 | `data/dev/rappel_alignement_a_annoter_v1.csv` | 0/60 | 60 | P/R d'alignement |
| 8 | `data/dev/double_annotation/*.csv` | modèles vides créés | 50 / 30 / 30 | kappa, accord NER |

---

## 1. Lexique tunisien → arabe standard

- **Chemin** : `data/dev/lexique_tunisien_v1.csv`
- **Colonnes** : `tunisien,standard,commentaire`
- **Exemples** (les 5 lignes actuelles sont des modèles proposés par l'assistant, **à valider**) :

  ```
  خدمة,شغل,« travail » (5edma)
  خدام,عامل,« travailleur »
  كونجي,عطلة,« congé » (emprunt au français)
  ```
- **Lignes conseillées** : 150 à 300.
- **Conseil** : ajouter aussi les **formes produites par la translittération arabizi**
  (affichées dans « Voir les étapes », étape 2). Exemple observé : « 5edma » donne « خدمة »,
  qui ne trouve « شغل » que si cette ligne existe. C'est la principale piste pour les
  questions arabizi (rappel 2/6 sur le dev).

## 2. Synonymes juridiques

- **Chemin** : `data/dev/synonymes_juridiques_v1.csv`
- **Colonnes** : `terme,synonyme,langue,commentaire` (paire appliquée dans les deux sens)
- **Exemples** (modèles actuels, **à valider**) :

  ```
  hebdomadaire,semaine,fr,
  virer,licencier,fr,
  patron,employeur,fr,
  ```
- **Lignes conseillées** : 50 à 100 paires.
- **À vérifier en priorité** : `légale,normale` fait monter l'article 90 devant le 79, et
  `salarié,travailleur` fait perdre la question D07 (voir `reports/erreurs_analysees_dev.csv`).

## 3. Questions arabes, tunisiennes et arabizi

- **Chemin** : `data/dev/questions_dev_v3_multilingue.csv` (à créer), puis un test gelé
  séparé `data/test_locked/questions_reference_v3.csv` écrit **avant** toute mesure.
- **Colonnes** (identiques au dev v2) : `id,langue,type,question,article_reference,reponse_attendue`
  avec `langue` ∈ `ar` / `tun` / `arabizi` et `type` ∈ `dans_perimetre` / `hors_perimetre`.
- **Exemples de format** (lignes réelles du dev v2) :

  ```
  D13,tun,dans_perimetre,"Ken el congé mta3i 5 ayem ouvrables, lezem ykoun mtawel wela yemken yet9assem ?",118,...
  D27,ar,hors_perimetre,ما هي شروط الحصول على رخصة السياقة؟,n/a,...
  D01,fr,dans_perimetre,Que peut obtenir un salarié en cas de rupture abusive de son contrat de travail ?,23,...
  ```
- **Lignes conseillées** : dev = 20 AR + 20 tunisien en écriture arabe + 20 arabizi,
  dont environ 2/3 dans le périmètre ; test gelé de même taille. Aujourd'hui le dev v2
  ne contient **aucune** question arabe dans le périmètre : le rappel arabe n'est pas mesurable.

## 4. Fautes d'orthographe réelles

- **Chemin** : `data/dev/questions_fautes_manuelles_v1.csv` (à créer)
- **Colonnes** : `id_source,question_avec_fautes,type_faute,commentaire`
  (`id_source` = identifiant du dev v2 ; `type_faute` ∈ `frappe` / `accent` / `phonétique` / `sigle`)
- **Exemples de format** (fautes **synthétiques** déjà générées, graine 2026, à remplacer
  par des fautes écrites par des personnes) :

  ```
  D05,"Dans quel délai se prescrivent les actions entre employeurs et slaariés nées des rleations de travail ?",frappe,
  D06,Quelles sont les atrtibutions des ocnseils de prud'hommes ?,frappe,
  D10,Un travapil commandé et non phublié doit-il être payé ?,frappe,
  ```
- **Lignes conseillées** : 56 (une par question du dev v2), écrites par quelqu'un qui ne
  regarde pas la question d'origine en tapant (dictée), pour obtenir des fautes naturelles.

## 5. Obligations (gold)

- **Chemins** : `data/dev/obligations_candidats_dev_v1.csv` (200 phrases) et
  `data/test_locked/obligations_candidats_test_v1.csv` (100 phrases, **à annoter en dernier**,
  une fois les règles figées).
- **Colonnes** : `obligation_id,article_fr,page_fr,phrase,qui,modal,quoi,quand,commentaire`
  (`modal` ∈ `obligation` / `interdiction` / `permission` ; `non_obligation` dans `commentaire`).
- **Schémas de format** (comme dans le guide, **pas des annotations du corpus**) :

  ```
  O###,FR-n,p,"L'employeur est tenu de … dans un délai de …",l'employeur,obligation,…,dans un délai de …,
  O###,FR-n,p,"Il est interdit à l'employeur de …",l'employeur,interdiction,…,,
  O###,FR-n,p,"La somme doit être versée …",,,,,non_obligation
  ```
- **Lignes** : 200 dev + 100 test (prévu par le guide).
- **Point à trancher** : le guide dit de saisir dans `obligations_modele_v1.csv` (vide),
  alors que les 200 phrases sont dans `obligations_candidats_dev_v1.csv`. Choisir un seul
  fichier et garder les mêmes `obligation_id` pour le kappa.

## 6. Entités nommées (NER)

- **Chemin** : `data/dev/ner_a_annoter_v1.csv` (60 phrases)
- **Colonnes** : `item_id,article_fr,page_fr,phrase,entites,commentaire`
  avec `entites` = `debut|fin|TYPE;…` (positions de caractères dans `phrase`, base 0, fin exclue ;
  types `ROLE`, `INSTITUTION`, `DELAI`, `MONTANT`).
- **Schémas de format** (phrase fictive « L'employeur doit payer 50 dinars dans les quinze jours. ») :

  ```
  0|11|ROLE            « L'employeur »
  23|32|MONTANT        « 50 dinars »
  33|54|DELAI          « dans les quinze jours »
  ```
- **Lignes conseillées** : 60 au minimum ; **200 ou plus** pour entraîner un CRF qui
  apprenne réellement (60 phrases suffisent seulement pour un premier test).
- **Conseil** : vérifier les positions avec un petit script (`phrase[debut:fin]`) avant de committer.

## 7. Rappel de l'alignement AR/FR

- **Chemin** : `data/dev/rappel_alignement_a_annoter_v1.csv` (60 articles arabes)
- **Colonnes** : `item_id,article_ar,numero_ar,page_ar,debut_texte_ar,article_fr_attendu,verdict_image,commentaire`
- **Exemples de format** : `article_fr_attendu` au format `FR-n` ou `FR-n-suffixe` vérifié
  sur l'image de la page ; `verdict_image` : valeurs à fixer par vous (le dev v1 utilise `correct`).

  ```
  R001,AR-5,5,10,"الفصل 5.- …",FR-…,correct,vu p.10 et p.…
  R002,AR-13,13,14,"الفصل 13.- …",FR-…,correct,
  R0xx,AR-…,…,…,"…",,absent,pas d'équivalent français trouvé
  ```
- **Lignes** : 60 (fichier déjà préparé).

## 8. Double annotation pour le kappa

- **Chemins** (modèles vides créés, échantillon tiré avec la graine 2026) :
  - `data/dev/double_annotation/obligations_annotateur_B.csv` : 50 phrases ;
  - `data/dev/double_annotation/ner_annotateur_B.csv` : 30 phrases ;
  - `data/dev/double_annotation/rappel_alignement_annotateur_B.csv` : 30 articles.
- **Colonnes** : identiques au fichier principal ; seuls les champs d'annotation sont vides.
- **Règle** : un **autre membre** que l'annotateur principal remplit ces fichiers, **sans
  regarder** les annotations du premier.
- **Calcul** (le script refuse si un des deux fichiers est vide) :

  ```
  python src/evaluation/calculer_kappa.py --a data/dev/obligations_candidats_dev_v1.csv --b data/dev/double_annotation/obligations_annotateur_B.csv --id obligation_id --champ modal
  python src/evaluation/calculer_kappa.py --a data/dev/rappel_alignement_a_annoter_v1.csv --b data/dev/double_annotation/rappel_alignement_annotateur_B.csv --id item_id --champ verdict_image
  python src/evaluation/calculer_kappa.py --mode spans --a data/dev/ner_a_annoter_v1.csv --b data/dev/double_annotation/ner_annotateur_B.csv --id item_id --champ entites
  ```
- **Effectif** : 50 items au minimum pour un kappa présentable ; en dessous, le script
  affiche un avertissement.
