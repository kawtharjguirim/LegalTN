"""Encodage, matrice de similarité et stratégies d'appariement AR -> FR."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from .donnees import RACINE

CACHE = RACINE / "runs/cache_embeddings"

# Préfixes attendus par la famille e5 (tâche symétrique : « query: » des deux côtés).
PREFIXES = {"intfloat/multilingual-e5-base": "query: ", "intfloat/multilingual-e5-large": "query: "}


def encoder(modele, nom_modele: str, textes: list[str], lot: int = 16,
            max_len: int = 256) -> np.ndarray:
    """Embeddings L2-normalisés, mis en cache selon (modèle, textes, longueur max)."""
    prefixe = PREFIXES.get(nom_modele, "")
    textes = [prefixe + t for t in textes]
    cle = hashlib.sha256(
        (nom_modele + f"|{max_len}|" + "\x1f".join(textes)).encode("utf-8")).hexdigest()[:20]
    chemin = CACHE / f"{cle}.npy"
    if chemin.exists():
        return np.load(chemin)
    modele.max_seq_length = max_len
    emb = modele.encode(textes, batch_size=lot, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=False)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(chemin, emb.astype(np.float32))
    return emb.astype(np.float32)


def bonus_numerotation(num_ar: list, num_fr: list) -> np.ndarray:
    """Matrice 1 si les numéros d'article (hors suffixe) coïncident, 0 sinon."""
    a = np.array([-1 if n is None else n for n in num_ar])[:, None]
    f = np.array([-2 if n is None else n for n in num_fr])[None, :]
    return (a == f).astype(np.float32)


def apparier(sim: np.ndarray, methode: str = "hongrois", seuil: float = 0.0) -> dict[int, int]:
    """Retourne {indice AR: indice FR} selon la stratégie :

    - ``argmax`` : meilleur FR pour chaque AR (un FR peut être pris plusieurs fois) ;
    - ``mutuel`` : ne garde que les couples meilleurs l'un pour l'autre ;
    - ``hongrois`` : affectation 1-1 maximisant la similarité totale.
    Les couples sous ``seuil`` sont rejetés (abstention).
    """
    if methode == "argmax":
        j = sim.argmax(1)
        couples = {i: int(j[i]) for i in range(sim.shape[0])}
    elif methode == "mutuel":
        j, i_inv = sim.argmax(1), sim.argmax(0)
        couples = {i: int(j[i]) for i in range(sim.shape[0]) if i_inv[j[i]] == i}
    elif methode == "hongrois":
        lignes, colonnes = linear_sum_assignment(-sim)
        couples = dict(zip(lignes.tolist(), colonnes.tolist()))
    else:
        raise ValueError(methode)
    return {i: j for i, j in couples.items() if sim[i, j] >= seuil}
