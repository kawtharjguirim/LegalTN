# LLM-juge de fidélité — palier Gold (21 novembre 2026)

Commandes :
```
python -X utf8 -m src.juge.juge echantillon      # 56 réponses tirées de l'audit Gold
python -X utf8 -m src.juge.juge appliquer        # jugements de référence -> verdict_claude
python -X utf8 -m src.juge.juge juger --modele qwen2.5:7b   (puis qwen2.5:3b)
```

## Question

Peut-on confier à un LLM local la vérification de la **fidélité** d'une réponse de LegalTN à
l'article qu'elle cite, c'est-à-dire ce que les métriques Silver (référence citée, citation
inventée) ne mesurent pas ? Exemple déjà vu au Silver : réponse sur le congé fractionné qui cite
le bon article mais lui fait dire le contraire.

## Protocole

- **Échantillon** : 56 réponses de qwen2.5:3b (citation forcée) issues de l'audit Gold final,
  questions dans le périmètre, réponse donnée, une seule répétition : 29 FR, 27 AR ;
  originales et paraphrases. Pour chacune, le texte des articles cités.
- **Référence** : verdict `fidele` / `partiel` / `infidele` posé par **Claude**, jugé d'après les
  seuls articles cités, **avant** toute exécution du juge (`juge_jugements_claude_v1.json`, avec
  une justification par réponse non fidèle). Distribution : 32 fidèles, 11 partielles,
  13 infidèles. **Pas encore relu par un humain** : la colonne `verdict_humain` est vide.
- **Juges** : qwen2.5:7b et qwen2.5:3b via Ollama, température 0, consigne en français avec
  définition des trois verdicts et un exemple de sortie.
- **Accord** : kappa de Cohen (3 classes, et binaire « fidèle / non fidèle »), par langue.

## Résultats (consigne v2)

| Juge | Accord brut | κ 3 classes | κ fidèle / non | κ FR | κ AR | Infidèles détectés | Latence |
|---|---:|---:|---:|---:|---:|---:|---:|
| **qwen2.5:7b** | 0,679 | **0,448** | **0,456** | 0,396 | 0,500 | **13 / 13** | 8,3 s |
| qwen2.5:3b | 0,554 | 0,150 | 0,197 | 0,181 | 0,118 | 4 / 13 (5 jugées fidèles) | 1,2 s |

Matrice qwen2.5:7b (lignes = référence, colonnes = juge) :

| | fidèle | partiel | infidèle |
|---|---:|---:|---:|
| fidèle (32) | 24 | 2 | 6 |
| partiel (11) | 7 | 1 | 3 |
| infidèle (13) | 0 | 0 | **13** |

En binaire « infidèle / autre », qwen2.5:7b obtient κ ≈ 0,64 : rappel 13/13, précision 13/22.

## Lecture

1. **qwen2.5:7b est un bon filtre d'alerte, pas encore un juge** : il signale **toutes** les
   réponses infidèles de l'échantillon (dont les deux réponses arabes contradictoires sur le
   fractionnement du congé, la retenue sur salaire et le rythme de paie). En revanche, il produit
   **6 fausses alertes sur 32 réponses fidèles** et ne sait pas distinguer « partiel » : 7 réponses
   partielles sur 11 sont jugées fidèles. Accord **modéré** (κ ≈ 0,45, échelle de Landis et Koch).
2. **qwen2.5:3b n'est pas utilisable comme juge** : κ ≈ 0,15, et il valide 5 réponses infidèles
   (J02, J08, J24, J30, J41). Le modèle qui rédige ne peut pas se juger lui-même.
3. Usage proposé : qwen2.5:7b en **contrôle a posteriori** (ou hors ligne sur l'audit) pour
   signaler les réponses à relire ; pas pour bloquer une réponse dans la démo (8 s de plus, et
   une réponse fidèle sur cinq serait bloquée à tort).

## Incident de format (consigne v1, conservée dans `v1_consigne_verdict/`)

Première consigne : « Réponds : VERDICT: FIDELE… ». Les deux modèles répondaient souvent
« INFIDELE | … » sans le préfixe, ou avec un mot déformé (« VERDILE ») : **32 verdicts sur 56
illisibles avec le 7B, 44 avec le 3B**, donc κ apparents de 0,08 et 0,05. Correctif : consigne
« commence par exactement un de ces trois mots » + exemple, lecture du premier des trois mots
(frontière de mot, « INFIDELE » ne se lit pas « FIDELE »). Aucun verdict illisible en v2.
La consigne a été modifiée après avoir vu les résultats v1 sur cet échantillon : les chiffres v2
sont légèrement optimistes.

## Limites

- **Référence posée par Claude, pas par un humain** : le kappa mesure l'accord avec Claude. Pour
  valider le juge, remplir `verdict_humain` dans `data/a_annoter/juge_echantillon_v1.csv` (les
  commentaires de Claude aident), puis relancer `juger` : le kappa humain est calculé
  automatiquement.
- 56 réponses, une seule exécution par juge alors que ces LLM ne sont pas déterministes
  (cf. Silver) : intervalle de confiance large sur κ.
- Le juge ne voit que les articles cités : une réponse juste en droit mais qui cite le mauvais
  article (J32) est jugée infidèle, ce qui est voulu ici.
