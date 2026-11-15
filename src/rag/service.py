"""Moteur de démonstration Silver : recherche hybride BM25 + e5, abstention par langue,
citation bilingue et étapes visibles. Même format de réponse que la démo Bronze.

Seuils d'abstention : configuration « hybride[multilingual-e5-base]+seuil_par_langue » de
``reports/silver/rag/ablations_rag.csv`` (réglés sur tout le dev v2 + questions AR
traduites ; performance mesurée en leave-one-out dans ``RESULTATS.md``).
Une question en écriture latine (français ou tunisien) prend le seuil français.
"""

from __future__ import annotations

from .recherche import Recherche

MODELE = "intfloat/multilingual-e5-base"
SEUILS = {"ar": 0.822, "fr": 0.860}
NOMS_LANGUE = {"fr": "français", "ar": "arabe"}


class MoteurHybride:
    nom = "hybride"

    def __init__(self, modele: str = MODELE, seuils: dict | None = None):
        self.recherche = Recherche(modele)
        self.seuils = seuils or SEUILS
        self.corpus = self.recherche.corpus

    def articles_indexes(self) -> dict:
        return {lg: len(c.articles) for lg, c in self.corpus.items()}

    def autre_langue(self, article: str, langue: str) -> dict | None:
        """Article de même intitulé dans l'autre langue (citation bilingue)."""
        autre = "ar" if langue == "fr" else "fr"
        i = self.recherche._index(autre, article)
        if i is None:
            return None
        art = self.corpus[autre].articles[i]
        return {"langue": autre, "page": art["page"], "texte": art["texte"]}

    def repondre(self, question: str, k: int = 3) -> dict:
        resultats, sig = self.recherche.rechercher(question, mode="hybride", bilingue=False, k=k)
        langue = sig["langue"]
        seuil = self.seuils[langue]
        abstention = not resultats or sig["cos_max"] < seuil
        etapes = [
            f"Langue détectée : {NOMS_LANGUE[langue]}",
            f"BM25 : meilleur score {sig.get('bm25_max', 0.0):.2f}",
            f"Recherche dense e5 : similarité max {sig['cos_max']:.3f} (seuil {seuil:.3f})",
            "Fusion des classements (RRF, k = 60)",
            "Abstention : question hors du Code du travail" if abstention
            else f"Citation : article {resultats[0].article}",
        ]
        candidats = [] if abstention else [
            {"article": r.article, "texte": r.texte, "page": r.page, "score": round(r.score, 4),
             "autre_langue": self.autre_langue(r.article, r.langue)}
            for r in resultats]
        return {"abstention": abstention, "langue": langue, "candidats": candidats,
                "moteur": self.nom, "etapes": etapes,
                "signaux": {"similarite_max": round(sig["cos_max"], 4), "seuil": seuil}}


