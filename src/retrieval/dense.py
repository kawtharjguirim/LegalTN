"""Recherche dense multilingue : un encodeur pré-entraîné compare la question aux articles FR et AR.

Recherche croisée : la question (FR, AR ou tunisien) est comparée aux deux index ; chaque article
reçoit le meilleur score obtenu dans l'une ou l'autre langue (les numéros d'articles sont communs).

Modèle par défaut : intfloat/multilingual-e5-base (préfixes « query: » / « passage: » exigés par e5).
Les vecteurs sont mis en cache dans data/processed/cache_dense/ (ignoré par git) ; le nom du
fichier contient l'empreinte des textes, donc un corpus modifié force un recalcul.

Limite connue : l'encodeur tronque à 512 jetons ; la fin des articles très longs n'est pas encodée.

Usage :
  python -X utf8 src/retrieval/dense.py --construire-index
  python -X utf8 src/retrieval/dense.py "Quel est le préavis pour rompre un CDI ?"
"""
import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src"))

MODELE_DEFAUT = "intfloat/multilingual-e5-base"
CACHE = RACINE / "data" / "processed" / "cache_dense"
GRAINE = 2026


def _prefixes(modele):
    return ("query: ", "passage: ") if "e5" in modele.lower() else ("", "")


class IndexDense:
    def __init__(self, corpus, modele=MODELE_DEFAUT, appareil="cpu"):
        from sentence_transformers import SentenceTransformer
        import torch
        torch.manual_seed(GRAINE)
        self.nom_modele = modele
        self.modele = SentenceTransformer(modele, device=appareil)
        self.pref_q, self.pref_p = _prefixes(modele)
        self.langues = {}
        for langue, c in corpus.items():
            textes = [a["texte"] for a in c.articles]
            self.langues[langue] = {
                "labels": [a["article"] for a in c.articles],
                "vecteurs": self._encoder_corpus(langue, textes),
            }

    def _encoder_corpus(self, langue, textes):
        empreinte = hashlib.sha256("\x1e".join(textes).encode("utf-8")).hexdigest()[:12]
        slug = self.nom_modele.replace("/", "__")
        chemin = CACHE / f"{slug}_{langue}_{empreinte}.npy"
        if chemin.exists():
            return np.load(chemin)
        vecteurs = self.modele.encode([self.pref_p + t for t in textes], batch_size=16,
                                      normalize_embeddings=True, show_progress_bar=True)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(chemin, vecteurs)
        return vecteurs

    def encoder_question(self, question):
        return self.modele.encode([self.pref_q + question], normalize_embeddings=True)[0]

    def classer(self, question, langues=None):
        """Retourne [(article, score cosinus)] trié, meilleur score par article sur les langues demandées."""
        q = self.encoder_question(question)
        meilleur = {}
        for langue, idx in self.langues.items():
            if langues and langue not in langues:
                continue
            sims = idx["vecteurs"] @ q
            for lab, s in zip(idx["labels"], sims):
                s = float(s)
                if s > meilleur.get(lab, -2.0):
                    meilleur[lab] = s
        return sorted(meilleur.items(), key=lambda x: -x[1])


def main():
    import repondre
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="*")
    p.add_argument("--modele", default=MODELE_DEFAUT)
    p.add_argument("--construire-index", action="store_true")
    a = p.parse_args()
    index = IndexDense(repondre.charger(), a.modele)
    if a.construire_index:
        for langue, idx in index.langues.items():
            print(f"{langue} : {idx['vecteurs'].shape[0]} articles, dimension {idx['vecteurs'].shape[1]}")
    question = " ".join(a.question).strip()
    if question:
        for lab, s in index.classer(question)[:5]:
            print(f"article {lab} : {s:.3f}")


if __name__ == "__main__":
    main()
