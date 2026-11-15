"""Évaluation et ablations de l'alignement AR <-> FR par embeddings (palier Silver).

Mesures sur les 160 paires gold vérifiées sur image (dev v1 + v2) :
- classement : P@1, R@5, MRR de l'article FR attendu pour chaque article AR ;
- appariement : précision / rappel des couples produits par une stratégie 1-1.
Accord global avec le pipeline Bronze (numérotation) sur ses 494 couples.

Biais à garder en tête : les paires gold ont été tirées parmi les sorties de la
numérotation puis validées ; la numérotation y est donc correcte par construction.
Ce script ne lit aucun fichier de data/test_locked.

Usage : python -X utf8 -m src.alignement_embeddings.evaluer --sortie reports/silver/alignement
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import donnees as d
from .aligner import apparier, bonus_numerotation, encoder

MODELES = ["sentence-transformers/LaBSE", "intfloat/multilingual-e5-base"]
VARIANTES = ["brut", "sans_entete", "sans_entete_norm"]
METHODES = ["argmax", "mutuel", "hongrois"]
LAMBDAS = [0.0, 0.1, 0.3]


def metriques_classement(sim: np.ndarray, gold_i: np.ndarray, gold_j: np.ndarray) -> dict:
    lignes = sim[gold_i]
    cible = lignes[np.arange(len(gold_i)), gold_j][:, None]
    rang = (lignes > cible).sum(1) + 1
    return {"p_at_1": float((rang == 1).mean()), "r_at_5": float((rang <= 5).mean()),
            "mrr": float((1.0 / rang).mean())}


def metriques_appariement(couples: dict, gold: dict, reference: dict) -> dict:
    sur_gold = {i: couples[i] for i in gold if i in couples}
    corrects = sum(gold[i] == j for i, j in sur_gold.items())
    accord = sum(reference.get(i) == j for i, j in couples.items())
    return {
        "precision_gold": corrects / len(sur_gold) if sur_gold else 0.0,
        "rappel_gold": corrects / len(gold),
        "couples": len(couples),
        "accord_numerotation_precision": accord / len(couples) if couples else 0.0,
        "accord_numerotation_rappel": accord / len(reference),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=d.RACINE / "reports/silver/alignement")
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--modeles", nargs="*", default=MODELES)
    args = parser.parse_args()

    import torch
    from sentence_transformers import SentenceTransformer

    appareil = "cuda" if torch.cuda.is_available() else "cpu"
    ar, fr = d.corpus()
    id_vers_i = {a: i for i, a in enumerate(ar["article_id"])}
    gold_df = d.paires_gold()
    gold = {id_vers_i[a]: int(j) for a, j in zip(gold_df["article_ar"], gold_df["fr_ligne"])}
    gold_i, gold_j = np.array(list(gold)), np.array(list(gold.values()))
    ref_df = d.paires_numerotation()
    reference = {id_vers_i[a]: int(j) for a, j in zip(ref_df["article_ar"], ref_df["fr_ligne"])}
    bonus = bonus_numerotation([d.numero_ar(t) for t in ar["texte_ar"]],
                               [d.numero_fr(t) for t in fr["texte_fr"]])

    resultats = []
    # Référence Bronze : la numérotation seule, appariée comme les embeddings.
    for methode in METHODES:
        couples = apparier(bonus, methode, seuil=0.5)
        resultats.append({"modele": "numerotation_seule", "variante": "-", "lambda": None,
                          "methode": methode, **metriques_classement(bonus, gold_i, gold_j),
                          **metriques_appariement(couples, gold, reference)})

    meilleures = {}
    for nom in args.modeles:
        modele = SentenceTransformer(nom, device=appareil)
        if appareil == "cuda":
            modele.half()
        for variante in VARIANTES:
            debut = time.perf_counter()
            e_ar = encoder(modele, nom, d.preparer(ar["texte_ar"].tolist(), "ar", variante),
                           max_len=args.max_len)
            e_fr = encoder(modele, nom, d.preparer(fr["texte_fr"].tolist(), "fr", variante),
                           max_len=args.max_len)
            duree = time.perf_counter() - debut
            sim = e_ar @ e_fr.T
            for lam in LAMBDAS:
                s = sim + lam * bonus
                classement = metriques_classement(s, gold_i, gold_j)
                for methode in METHODES:
                    couples = apparier(s, methode)
                    resultats.append({
                        "modele": nom, "variante": variante, "lambda": lam, "methode": methode,
                        **classement, **metriques_appariement(couples, gold, reference),
                        "encodage_s": round(duree, 2),
                    })
            meilleures[(nom, variante)] = sim
        del modele
        if appareil == "cuda":
            torch.cuda.empty_cache()

    args.sortie.mkdir(parents=True, exist_ok=True)
    tableau = pd.DataFrame(resultats)
    tableau.round(4).to_csv(args.sortie / "ablations_alignement.csv", index=False)

    # Analyse d'erreurs : embeddings purs (sans en-tête, sans bonus, variante la meilleure), méthode hongroise,
    # comparés à la numérotation. Chaque désaccord est à catégoriser à la main.
    prep_ar = d.preparer(ar["texte_ar"].tolist(), "ar", "sans_entete")
    prep_fr = d.preparer(fr["texte_fr"].tolist(), "fr", "sans_entete")
    num_fr = [d.numero_fr(t) for t in fr["texte_fr"]]

    def categorie(i, j_ref, j):
        """Pré-catégorisation automatique, à confirmer à la main."""
        if len(prep_ar[i]) < 15 or len(prep_fr[j_ref]) < 15:
            return "texte vide apres en-tete (abroge)"
        if j is not None and num_fr[j] == num_fr[j_ref]:
            return "sous-article de meme numero"
        if j is None:
            return "abstention (aucun FR libre)"
        arabe = sum("؀" <= c <= "ۿ" for c in prep_ar[i]) / max(1, len(prep_ar[i]))
        if arabe < 0.75:
            return "OCR arabe bruite"
        return "a examiner (contenu proche)"

    for nom in args.modeles:
        sim = meilleures[(nom, "sans_entete")]
        couples = apparier(sim, "hongrois")
        lignes = []
        for i, j_ref in sorted(reference.items()):
            j = couples.get(i)
            if j == j_ref:
                continue
            lignes.append({
                "article_ar": ar.at[i, "article_id"], "page_ar": ar.at[i, "page"],
                "fr_numerotation": fr.at[j_ref, "article_id"], "fr_ligne_numerotation": j_ref,
                "fr_embeddings": fr.at[j, "article_id"] if j is not None else "",
                "fr_ligne_embeddings": j, "sim_numerotation": round(float(sim[i, j_ref]), 4),
                "sim_embeddings": round(float(sim[i, j]), 4) if j is not None else None,
                "dans_gold": i in gold,
                "texte_ar": ar.at[i, "texte_ar"][:200],
                "texte_fr_numerotation": fr.at[j_ref, "texte_fr"][:200],
                "texte_fr_embeddings": fr.at[j, "texte_fr"][:200] if j is not None else "",
                "categorie_auto": categorie(i, j_ref, j), "categorie": "", "commentaire": "",
            })
        court = nom.split("/")[-1]
        pd.DataFrame(lignes).to_csv(args.sortie / f"desaccords_{court}.csv", index=False,
                                    encoding="utf-8")

    with open(args.sortie / "configuration.json", "w", encoding="utf-8") as f:
        json.dump({"modeles": args.modeles, "variantes": VARIANTES, "methodes": METHODES,
                   "lambdas": LAMBDAS, "max_len": args.max_len, "appareil": appareil,
                   "n_gold": len(gold), "n_reference_numerotation": len(reference),
                   "n_ar": len(ar), "n_fr": len(fr)}, f, ensure_ascii=False, indent=2)

    colonnes = ["modele", "variante", "lambda", "methode", "p_at_1", "r_at_5", "mrr",
                "precision_gold", "rappel_gold", "accord_numerotation_precision"]
    print(tableau[tableau["methode"] == "hongrois"][colonnes].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
