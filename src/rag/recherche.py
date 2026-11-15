"""Recherche d'articles : BM25 (Bronze), dense multilingue, hybride (RRF), mono ou bilingue.

Les intitulés d'articles (« 14 bis ») sont communs aux corpus FR et AR : ils servent de
clé de fusion entre langues, sans passer par le fichier d'alignement.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src/demo"))
import repondre  # noqa: E402  (démo Bronze : corpus, BM25, détection de langue)

CACHE = RACINE / "runs/cache_embeddings"
PREFIXE_REQUETE = {"intfloat/multilingual-e5-base": "query: ", "intfloat/multilingual-e5-large": "query: "}
PREFIXE_PASSAGE = {"intfloat/multilingual-e5-base": "passage: ", "intfloat/multilingual-e5-large": "passage: "}
K_RRF = 60


@dataclass
class Resultat:
    article: str
    score: float
    langue: str
    page: str
    texte: str
    details: dict = field(default_factory=dict)


def rrf(classements: list[list[str]], k: int = K_RRF) -> dict[str, float]:
    """Reciprocal Rank Fusion : somme de 1 / (k + rang) sur les classements."""
    scores: dict[str, float] = {}
    for classement in classements:
        for rang, lab in enumerate(classement, 1):
            scores[lab] = scores.get(lab, 0.0) + 1.0 / (k + rang)
    return scores


def dedoublonner(indices, scores, articles) -> list[tuple[str, float, int]]:
    """Classement par intitulé (meilleure ligne gardée) : [(intitulé, score, indice)]."""
    vus, sortie = set(), []
    for i in indices:
        lab = articles[i]["article"]
        if lab not in vus:
            vus.add(lab)
            sortie.append((lab, float(scores[i]), int(i)))
    return sortie


class Recherche:
    def __init__(self, nom_modele: str | None = "intfloat/multilingual-e5-base",
                 appareil: str | None = None):
        self.corpus = repondre.charger()  # {"fr": Corpus, "ar": Corpus}
        self.nom_modele = nom_modele
        self.modele = None
        self.emb = {}
        if nom_modele:
            from sentence_transformers import SentenceTransformer
            import torch

            appareil = appareil or ("cuda" if torch.cuda.is_available() else "cpu")
            self.modele = SentenceTransformer(nom_modele, device=appareil)
            self.modele.max_seq_length = 512
            for lg, c in self.corpus.items():
                self.emb[lg] = self._encoder_passages([a["texte"] for a in c.articles])

    def _encoder_passages(self, textes: list[str]) -> np.ndarray:
        prefixe = PREFIXE_PASSAGE.get(self.nom_modele, "")
        textes = [prefixe + " ".join(t.split()) for t in textes]
        cle = hashlib.sha256((self.nom_modele + "|512|" + "\x1f".join(textes)).encode()).hexdigest()[:20]
        chemin = CACHE / f"passages_{cle}.npy"
        if chemin.exists():
            return np.load(chemin)
        emb = self.modele.encode(textes, batch_size=16, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(chemin, emb)
        return emb

    def encoder_requete(self, question: str) -> np.ndarray:
        prefixe = PREFIXE_REQUETE.get(self.nom_modele, "")
        return self.modele.encode([prefixe + question], normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False)[0]

    # -------------------------------------------------------------- classements
    def bm25(self, question: str, langue: str) -> list[tuple[str, float, int]]:
        c = self.corpus[langue]
        ordre, scores, requete = c.classer(question)
        if not requete or not any(t in c.bm.df for t in requete):
            return []
        return dedoublonner(ordre, scores, c.articles)

    def dense(self, question: str, langue: str, q: np.ndarray | None = None):
        q = self.encoder_requete(question) if q is None else q
        sims = self.emb[langue] @ q
        return dedoublonner(np.argsort(-sims), sims, self.corpus[langue].articles)

    def rechercher(self, question: str, mode: str = "hybride", bilingue: bool = True,
                   k: int = 5) -> tuple[list[Resultat], dict]:
        """Classement final et signaux d'abstention (meilleur cosinus, meilleur BM25)."""
        langue = repondre.detecter_langue(question)
        langues = ["fr", "ar"] if bilingue else [langue]
        q = self.encoder_requete(question) if mode in {"dense", "hybride"} else None
        classements, signaux, meilleurs = [], {"langue": langue}, {}
        for lg in langues:
            if mode in {"bm25", "hybride"} and lg == langue:
                c_bm = self.bm25(question, lg)
                classements.append([lab for lab, _, _ in c_bm])
                signaux["bm25_max"] = c_bm[0][1] if c_bm else 0.0
                for lab, s, i in c_bm[:50]:
                    meilleurs.setdefault(lab, (lg, i))
            if mode in {"dense", "hybride"}:
                c_de = self.dense(question, lg, q)
                classements.append([lab for lab, _, _ in c_de])
                signaux[f"cos_max_{lg}"] = c_de[0][1]
                for lab, s, i in c_de[:50]:
                    meilleurs.setdefault(lab, (lg, i))
        signaux["cos_max"] = max((v for k_, v in signaux.items() if k_.startswith("cos_max_")),
                                 default=0.0)
        fusion = rrf(classements) if len(classements) > 1 else {
            lab: 1.0 / (K_RRF + r) for r, lab in enumerate(classements[0] if classements else [], 1)}
        ordre = sorted(fusion, key=lambda lab: -fusion[lab])[:k]
        sortie = []
        for lab in ordre:
            # Citation dans la langue de la question si l'article y existe, sinon l'autre.
            lg_cit = langue if self._index(langue, lab) is not None else meilleurs.get(lab, (langue,))[0]
            i = self._index(lg_cit, lab)
            art = self.corpus[lg_cit].articles[i]
            sortie.append(Resultat(lab, fusion[lab], lg_cit, art["page"], art["texte"]))
        return sortie, signaux

    def _index(self, langue: str, lab: str) -> int | None:
        if not hasattr(self, "_par_label"):
            self._par_label = {
                lg: {a["article"]: i for i, a in reversed(list(enumerate(c.articles)))}
                for lg, c in self.corpus.items()}
        return self._par_label[langue].get(lab)
