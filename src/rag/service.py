"""Moteur de démonstration Silver : recherche hybride BM25 + e5, abstention par langue,
citation bilingue, étapes visibles et, si Ollama est disponible, réponse rédigée par un
LLM ouvert avec citation vérifiée et résumé en langage clair.

Seuils d'abstention : configuration « hybride[multilingual-e5-base]+seuil_par_langue » de
``reports/silver/rag/ablations_rag.csv`` (réglés sur tout le dev v2 + questions AR
traduites ; performance mesurée en leave-one-out dans ``RESULTATS.md``).
Une question en écriture latine (français ou tunisien) prend le seuil français.
"""

from __future__ import annotations

import time

from . import generer
from .recherche import Recherche

MODELE = "intfloat/multilingual-e5-base"
SEUILS = {"ar": 0.822, "fr": 0.860}
NOMS_LANGUE = {"fr": "français", "ar": "arabe"}
K_CONTEXTE_LLM = 3          # articles transmis au LLM
DELAI_VERIF_LLM = 60.0      # secondes entre deux vérifications de disponibilité d'Ollama


class MoteurHybride:
    nom = "hybride"

    def __init__(self, modele: str = MODELE, seuils: dict | None = None,
                 llm: str | None = generer.MODELE_DEFAUT):
        self.recherche = Recherche(modele)
        self.seuils = seuils or SEUILS
        self.corpus = self.recherche.corpus
        self.llm = llm
        self._llm_etat = (0.0, False)

    def articles_indexes(self) -> dict:
        return {lg: len(c.articles) for lg, c in self.corpus.items()}

    def llm_disponible(self) -> bool:
        if not self.llm:
            return False
        verifie_a, etat = self._llm_etat
        if time.monotonic() - verifie_a > DELAI_VERIF_LLM:
            etat = generer.disponible(self.llm)
            self._llm_etat = (time.monotonic(), etat)
        return etat

    def autre_langue(self, article: str, langue: str) -> dict | None:
        """Article de même intitulé dans l'autre langue (citation bilingue)."""
        autre = "ar" if langue == "fr" else "fr"
        i = self.recherche._index(autre, article)
        if i is None:
            return None
        art = self.corpus[autre].articles[i]
        return {"langue": autre, "page": art["page"], "texte": art["texte"]}

    def rediger(self, question: str, resultats, langue: str) -> tuple[dict | None, str]:
        """Réponse rédigée par le LLM (citation forcée et vérifiée) et étape à afficher."""
        if not self.llm_disponible():
            return None, "Rédaction LLM : indisponible (Ollama non démarré), extraits seuls"
        debut = time.perf_counter()
        try:
            r = generer.repondre(question, resultats[:K_CONTEXTE_LLM], langue,
                                 strategie="citation_forcee", modele=self.llm)
        except Exception as e:  # serveur arrêté entre-temps, délai dépassé...
            self._llm_etat = (0.0, False)
            return None, f"Rédaction LLM : échec ({type(e).__name__}), extraits seuls"
        duree = round((time.perf_counter() - debut) * 1000)
        lg = "ar" if langue == "ar" else "fr"
        redaction = {"texte": r["reponse"], "citations": r["citations"],
                     "abstention": r["abstention"], "modele": self.llm, "latence_ms": duree,
                     "avertissement": generer.AVERTISSEMENT[lg]}
        if r["abstention"]:
            etape = f"Rédaction LLM ({self.llm}) : pas de réponse appuyée sur les articles"
        else:
            etape = (f"Rédaction LLM ({self.llm}) : citation vérifiée, article "
                     f"{', '.join(r['citations'])}")
        return redaction, etape

    def repondre(self, question: str, k: int = 3, rediger: bool = True) -> dict:
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
        redaction = None
        if not abstention and rediger:
            redaction, etape = self.rediger(question, resultats, langue)
            etapes.append(etape)
        candidats = [] if abstention else [
            {"article": r.article, "texte": r.texte, "page": r.page, "score": round(r.score, 4),
             "autre_langue": self.autre_langue(r.article, r.langue)}
            for r in resultats]
        return {"abstention": abstention, "langue": langue, "candidats": candidats,
                "moteur": self.nom, "etapes": etapes, "reponse_redigee": redaction,
                "signaux": {"similarite_max": round(sig["cos_max"], 4), "seuil": seuil}}

    def resumer(self, article: str, langue: str) -> dict:
        """Résumé en langage clair d'un article indexé (LLM requis)."""
        lg = "ar" if langue == "ar" else "fr"
        i = self.recherche._index(lg, article)
        if i is None:
            raise KeyError(article)
        if not self.llm_disponible():
            raise RuntimeError("LLM indisponible : démarrer Ollama.")
        art = self.corpus[lg].articles[i]
        debut = time.perf_counter()
        texte = generer.resumer(article, art["texte"], lg, modele=self.llm)
        return {"article": article, "langue": lg, "resume": texte, "modele": self.llm,
                "avertissement": generer.AVERTISSEMENT[lg],
                "latence_ms": round((time.perf_counter() - debut) * 1000)}
