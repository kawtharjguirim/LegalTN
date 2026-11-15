"""Fusion de classements par Reciprocal Rank Fusion (RRF) et utilitaires de classement.

RRF (Cormack et al., 2009) : score(article) = somme sur les systèmes de 1 / (K_RRF + rang).
K_RRF = 60 est la valeur de l'article d'origine ; elle n'est pas réglée sur nos données.
Aucune dépendance externe : testable sans modèle neuronal.
"""

K_RRF = 60


def dedupliquer(labels):
    """Garde la première occurrence de chaque article, dans l'ordre."""
    vus, sortie = set(), []
    for lab in labels:
        if lab not in vus:
            vus.add(lab)
            sortie.append(lab)
    return sortie


def fusion_rrf(classements, k=K_RRF):
    """classements : listes d'articles, du plus au moins pertinent.

    Retourne [(article, score_rrf)] trié par score décroissant ; égalités départagées
    par le meilleur rang obtenu, puis par l'ordre d'apparition (déterministe).
    """
    scores, meilleur_rang, ordre = {}, {}, {}
    for classement in classements:
        for rang, lab in enumerate(dedupliquer(classement), start=1):
            scores[lab] = scores.get(lab, 0.0) + 1.0 / (k + rang)
            meilleur_rang[lab] = min(meilleur_rang.get(lab, rang), rang)
            ordre.setdefault(lab, len(ordre))
    return sorted(scores.items(), key=lambda x: (-x[1], meilleur_rang[x[0]], ordre[x[0]]))


def classement_bm25(corpus, question):
    """Articles classés par BM25 dans le corpus de la langue détectée (sans seuil)."""
    c = corpus
    ordre, _, termes = c.classer(question)
    if not termes or not any(t in c.bm.df for t in termes):
        return []
    return dedupliquer(c.articles[i]["article"] for i in ordre)
