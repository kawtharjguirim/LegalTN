"""Détection de divergences entre versions arabe et française des 494 articles appariés.

Trois signaux par paire (contenu sans l'intitulé numéroté ni les mentions de modification) :
- similarité LaBSE (modèle entraîné à repérer des traductions) : faible = suspect ;
- nombres différents (chiffres et nombres en lettres, hors « 1 ») : délai, montant, âge, renvoi ;
- rapport de longueur FR / AR anormal (écart à la médiane, en log).

Sortie : toutes les paires notées (``paires_scores.csv``) et un échantillon à juger :
les 12 similarités les plus faibles, les 12 plus forts écarts de nombres (hors doublons) et
10 paires tirées au hasard parmi les autres (témoins), graine fixe.

Usage : python -X utf8 -m src.divergences.detecter
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import re
from pathlib import Path

import numpy as np

from src.alignement_embeddings import donnees as d
from src.alignement_embeddings.aligner import encoder

from .nombres import nombres_ar, nombres_fr

RACINE = d.RACINE
GRAINE = 20261120
RE_NOTE_FR = re.compile(r"\((?:[^()]*(?:modifi|ajout|abrog|loi n)[^()]*)\)", re.IGNORECASE)
RE_NOTE_AR = re.compile(r"\((?:[^()]*(?:نقح|أضيف|اضيف|ألغي|الغي|بالقانون)[^()]*)\)")
RE_LOI_FR = re.compile(r"loi\s+n\s*°?\s*[\d-]+\s+du\s+\d+\s+\w+\s+\d{4}", re.IGNORECASE)
RE_LOI_AR = re.compile(r"(?:القانون|قانون)\s+عدد\s+\d+\s+لسنة\s+\d{4}(?:\s+المؤرخ\s+في\s+\d+\s+\S+\s+\d{4})?")


def nettoyer(texte: str, langue: str) -> str:
    t = d.preparer([texte], langue, "sans_entete")[0]
    if langue == "fr":
        return RE_LOI_FR.sub(" ", RE_NOTE_FR.sub(" ", t))
    return RE_LOI_AR.sub(" ", RE_NOTE_AR.sub(" ", t))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/divergences")
    parser.add_argument("--appareil", default="cpu")
    args = parser.parse_args()
    from sentence_transformers import SentenceTransformer

    ar, fr = d.corpus()
    id_vers_i = {a: i for i, a in enumerate(ar["article_id"])}
    paires = d.paires_numerotation()
    lignes = []
    for a_id, j in zip(paires["article_ar"], paires["fr_ligne"]):
        i = id_vers_i[a_id]
        t_ar, t_fr = nettoyer(ar.at[i, "texte_ar"], "ar"), nettoyer(fr.at[j, "texte_fr"], "fr")
        if len(t_ar) < 20 or len(t_fr) < 20:
            continue  # article abrogé ou vide : rien à comparer
        n_ar, n_fr = nombres_ar(t_ar) - {1}, nombres_fr(t_fr) - {1}
        lignes.append({"article_ar": a_id, "article_fr": fr.at[j, "article_id"], "fr_ligne": j,
                       "page_ar": ar.at[i, "page"], "page_fr": fr.at[j, "page"],
                       "t_ar": t_ar, "t_fr": t_fr, "nombres_ar": sorted(n_ar), "nombres_fr": sorted(n_fr),
                       "ecart_nombres": len(n_ar ^ n_fr)})

    modele = SentenceTransformer("sentence-transformers/LaBSE", device=args.appareil)
    e_ar = encoder(modele, "sentence-transformers/LaBSE", [l["t_ar"] for l in lignes])
    e_fr = encoder(modele, "sentence-transformers/LaBSE", [l["t_fr"] for l in lignes])
    log_ratio = [math.log(len(l["t_fr"]) / len(l["t_ar"])) for l in lignes]
    med = float(np.median(log_ratio))
    for k, l in enumerate(lignes):
        l["similarite"] = round(float(e_ar[k] @ e_fr[k]), 4)
        l["ecart_longueur"] = round(abs(log_ratio[k] - med), 3)

    # Échantillon à juger.
    par_sim = sorted(lignes, key=lambda l: l["similarite"])
    par_nb = sorted(lignes, key=lambda l: (-l["ecart_nombres"], l["similarite"]))
    choisis, vus = [], set()
    for source, liste, n in (("similarite_faible", par_sim, 12), ("nombres_differents", par_nb, 12)):
        for l in liste:
            if len([c for c in choisis if c[0] == source]) == n:
                break
            if l["article_ar"] not in vus:
                choisis.append((source, l))
                vus.add(l["article_ar"])
    reste = [l for l in lignes if l["article_ar"] not in vus]
    for l in random.Random(GRAINE).sample(reste, 10):
        choisis.append(("temoin_aleatoire", l))

    args.sortie.mkdir(parents=True, exist_ok=True)
    champs = ["article_ar", "article_fr", "fr_ligne", "page_ar", "page_fr", "similarite",
              "ecart_nombres", "nombres_ar", "nombres_fr", "ecart_longueur"]
    with open(args.sortie / "paires_scores.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(par_sim)
    ech = RACINE / "data/a_annoter/divergences_echantillon_v1.csv"
    if ech.exists():
        print(f"{ech.name} existe déjà (jugements possibles) : échantillon non réécrit.")
        return
    with open(ech, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "selection"] + champs + ["texte_ar", "texte_fr",
                                                                         "verdict", "type", "commentaire", "statut"])
        w.writeheader()
        for k, (source, l) in enumerate(choisis, 1):
            w.writerow({"id": f"DV{k:02d}", "selection": source, **{c: l[c] for c in champs},
                        "texte_ar": l["t_ar"], "texte_fr": l["t_fr"], "verdict": "", "type": "",
                        "commentaire": "", "statut": "a_juger"})
    sims = [l["similarite"] for l in lignes]
    print(f"{len(lignes)} paires comparées (abrogés exclus) ; similarité médiane {np.median(sims):.3f}, "
          f"min {min(sims):.3f} ; écart de nombres > 0 : {sum(l['ecart_nombres'] > 0 for l in lignes)}")
    print(f"échantillon : {len(choisis)} paires -> {ech}")


if __name__ == "__main__":
    main()
