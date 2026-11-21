"""Classification de domaine des articles du Code (12 domaines), macro-F1, FR et AR, transfert entre langues.

Étiquettes : structure du Code (``etiquettes.py``). Évaluation en **validation croisée par blocs** : les articles
voisins partagent vocabulaire et domaine, un découpage aléatoire article par article gonflerait les scores ;
on regroupe donc les articles par blocs de 6 numéros consécutifs, jamais séparés entre apprentissage et test,
et un article français et son équivalent arabe (même numéro) tombent dans le même pli. 5 plis, 3 graines
(la graine change l'affectation des blocs aux plis). Macro-F1 calculée sur les prédictions de tous les plis
d'une graine, puis moyenne et écart-type sur les 3 graines.

Systèmes : majorité ; TF-IDF + régression logistique (par langue) ; embeddings multilingual-e5-base + régression
logistique (par langue, bilingue, et **transfert** : apprendre sur une langue, tester sur l'autre).

Usage : python -X utf8 -m src.domaine.evaluer [--appareil cpu]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline

from .etiquettes import DOMAINES, charger

RACINE = Path(__file__).resolve().parents[2]
GRAINES = (0, 1, 2)
PLIS = 5
BLOC = 6
MODELE = "intfloat/multilingual-e5-base"
CACHE = RACINE / "runs/domaine_embeddings_e5.npz"


def embeddings(articles: list[dict], appareil: str) -> np.ndarray:
    """Embeddings e5 des textes (préfixe « query: », normalisés), mis en cache d'après les identifiants."""
    cles = [f'{a["langue"]}:{a["id"]}:{a["longueur"]}' for a in articles]
    if CACHE.exists():
        d = np.load(CACHE, allow_pickle=True)
        if list(d["cles"]) == cles:
            return d["emb"]
    from sentence_transformers import SentenceTransformer
    modele = SentenceTransformer(MODELE, device=appareil)
    modele.max_seq_length = 256
    emb = modele.encode(["query: " + a["texte"] for a in articles], batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    CACHE.parent.mkdir(exist_ok=True)
    np.savez(CACHE, cles=np.array(cles, dtype=object), emb=emb)
    return emb


def plis(numeros: list[int], graine: int) -> dict[int, int]:
    """Pli de chaque bloc de numéros (identique pour les deux langues)."""
    blocs = sorted({n // BLOC for n in numeros})
    random.Random(graine).shuffle(blocs)
    return {b: i % PLIS for i, b in enumerate(blocs)}


def tfidf_lr(langue: str):
    vect = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, min_df=2) if langue == "fr" else \
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)
    return make_pipeline(vect, LogisticRegression(C=10, max_iter=2000, class_weight="balanced"))


def lr():
    return LogisticRegression(C=10, max_iter=3000, class_weight="balanced")


def macro(y, p) -> float:
    return float(f1_score(y, p, labels=DOMAINES, average="macro", zero_division=0))


def evaluer(appareil: str = "cpu") -> dict:
    fr, ar = charger("fr"), charger("ar")
    tous = fr + ar
    emb = embeddings(tous, appareil)
    e_fr, e_ar = emb[:len(fr)], emb[len(fr):]
    y_fr, y_ar = np.array([a["domaine"] for a in fr]), np.array([a["domaine"] for a in ar])
    t_fr, t_ar = [a["texte"] for a in fr], [a["texte"] for a in ar]
    n_fr, n_ar = np.array([a["numero"] for a in fr]), np.array([a["numero"] for a in ar])
    systemes = ["majorite_fr", "majorite_ar", "tfidf_fr", "tfidf_ar", "e5_fr", "e5_ar", "e5_bilingue_fr", "e5_bilingue_ar", "transfert_fr_vers_ar", "transfert_ar_vers_fr"]
    pred = {s: {g: np.empty(len(y_fr if s.endswith("_fr") or s.endswith("vers_fr") else y_ar), dtype=object) for g in GRAINES} for s in systemes}
    res: dict = {"n_fr": len(fr), "n_ar": len(ar), "domaines": dict(Counter(y_fr)), "systemes": {}}
    for g in GRAINES:
        pli = plis(sorted(set(n_fr) | set(n_ar)), g)
        f_fr, f_ar = np.array([pli[n // BLOC] for n in n_fr]), np.array([pli[n // BLOC] for n in n_ar])
        for k in range(PLIS):
            tr_fr, te_fr, tr_ar, te_ar = f_fr != k, f_fr == k, f_ar != k, f_ar == k
            maj_fr, maj_ar = Counter(y_fr[tr_fr]).most_common(1)[0][0], Counter(y_ar[tr_ar]).most_common(1)[0][0]
            pred["majorite_fr"][g][te_fr], pred["majorite_ar"][g][te_ar] = maj_fr, maj_ar
            for lg, (t, y, tr, te) in {"fr": (t_fr, y_fr, tr_fr, te_fr), "ar": (t_ar, y_ar, tr_ar, te_ar)}.items():
                m = tfidf_lr(lg).fit([t[i] for i in np.flatnonzero(tr)], y[tr])
                pred[f"tfidf_{lg}"][g][te] = m.predict([t[i] for i in np.flatnonzero(te)])
            m_fr, m_ar = lr().fit(e_fr[tr_fr], y_fr[tr_fr]), lr().fit(e_ar[tr_ar], y_ar[tr_ar])
            pred["e5_fr"][g][te_fr], pred["e5_ar"][g][te_ar] = m_fr.predict(e_fr[te_fr]), m_ar.predict(e_ar[te_ar])
            mb = lr().fit(np.vstack([e_fr[tr_fr], e_ar[tr_ar]]), np.concatenate([y_fr[tr_fr], y_ar[tr_ar]]))
            pred["e5_bilingue_fr"][g][te_fr], pred["e5_bilingue_ar"][g][te_ar] = mb.predict(e_fr[te_fr]), mb.predict(e_ar[te_ar])
            pred["transfert_fr_vers_ar"][g][te_ar] = m_fr.predict(e_ar[te_ar])      # appris en français, testé en arabe
            pred["transfert_ar_vers_fr"][g][te_fr] = m_ar.predict(e_fr[te_fr])
    for s in systemes:
        y = y_ar if s.endswith("_ar") or s.endswith("vers_ar") else y_fr
        m = [macro(y, pred[s][g]) for g in GRAINES]
        a = [float(accuracy_score(y, pred[s][g])) for g in GRAINES]
        par_classe = {d: round(float(np.mean([f1_score(y, pred[s][g], labels=[d], average="macro", zero_division=0) for g in GRAINES])), 3) for d in DOMAINES}
        res["systemes"][s] = {"macro_f1": round(float(np.mean(m)), 4), "macro_f1_ecart_type": round(float(np.std(m)), 4), "macro_f1_par_graine": [round(x, 4) for x in m],
                              "exactitude": round(float(np.mean(a)), 4), "f1_par_classe": par_classe}
    meilleur = pred["e5_fr"][GRAINES[0]]
    res["matrice_e5_fr_graine0"] = {"classes": DOMAINES, "valeurs": confusion_matrix(y_fr, meilleur, labels=DOMAINES).tolist()}
    res["erreurs_e5_fr_graine0"] = [{"numero": int(a["numero"]), "vrai": a["domaine"], "predit": p} for a, p in zip(fr, meilleur) if a["domaine"] != p]
    return res


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appareil", default="cpu")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/domaine")
    args = parser.parse_args()
    res = evaluer(args.appareil)
    args.sortie.mkdir(parents=True, exist_ok=True)
    (args.sortie / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(args.sortie / "erreurs_e5_fr.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["numero", "vrai", "predit"])
        w.writeheader()
        w.writerows(res["erreurs_e5_fr_graine0"])
    print(f'{res["n_fr"]} articles FR, {res["n_ar"]} AR')
    for s, v in res["systemes"].items():
        print(f'{s:24s} macro-F1 {v["macro_f1"]:.3f} ± {v["macro_f1_ecart_type"]:.3f}  exactitude {v["exactitude"]:.3f}')


if __name__ == "__main__":
    main()
