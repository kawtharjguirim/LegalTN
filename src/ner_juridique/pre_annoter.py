"""Découpe le corpus en phrases, pré-annote par règles et prépare les lots à corriger.

Sorties (aucun fichier existant n'est écrasé sans --forcer) :
- ``data/silver/ner_silver_{fr,ar}.jsonl`` : phrases d'entraînement annotées par règles,
  hors articles des lots d'évaluation (même numéro d'article, dans les deux langues) ;
- ``data/a_annoter/ner_{dev,test}_{fr,ar}_v1.csv`` : 60 phrases par lot, pré-remplies,
  colonne ``statut`` à passer de ``a_verifier`` à ``verifie`` après correction humaine.

Le lot FR dev reprend les 60 phrases de ``data/dev/ner_a_annoter_v1.csv`` (fichier non modifié).
Tirage des autres lots : graine fixe, 70 % de phrases où les règles trouvent au moins
une entité, 30 % tirées sans condition (pour mesurer aussi les entités oubliées).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path

from .regles import annoter, lisible, vers_texte

RACINE = Path(__file__).resolve().parents[2]
GRAINE = 20261115
TAILLE_LOT = 60
LONGUEUR = (40, 400)

RE_FIN_FR = re.compile(r"(?<=[.;!?])\s+(?=[A-ZÉÈÀÂÔ«(0-9])")
RE_FIN_AR = re.compile(r"(?<=[.؛!?؟])\s+")
RE_NUM_FR = re.compile(r"^FR-(\d+)")
RE_NUM_AR = re.compile(r"^AR-(\d+)")


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def decouper(texte: str, langue: str) -> list[str]:
    texte = " ".join((texte or "").split())
    # Protège les abréviations courantes du français juridique.
    if langue == "fr":
        texte = re.sub(r"\b(n°|art|al|cf|etc)\.\s", r"\1§ ", texte, flags=re.I)
    morceaux = (RE_FIN_FR if langue == "fr" else RE_FIN_AR).split(texte)
    return [m.replace("§", ".").strip() for m in morceaux if m.strip()]


def phrases(langue: str) -> list[dict]:
    if langue == "fr":
        lignes, col, rx = lire(RACINE / "data/processed/articles_fr_corrige.csv"), "texte_fr", RE_NUM_FR
    else:
        lignes, col, rx = lire(RACINE / "data/processed/articles_ar.csv"), "texte_ar", RE_NUM_AR
    sortie = []
    for i, r in enumerate(lignes):
        if langue == "ar" and r.get("plage") == "True":
            continue
        m = rx.match(r["article_id"])
        for k, p in enumerate(decouper(r[col], langue)):
            sortie.append({"id": f"{langue}-{i:03d}-{k:02d}", "langue": langue,
                           "article": r["article_id"], "numero": int(m.group(1)) if m else None,
                           "page": r["page"], "phrase": p})
    return sortie


def tirer(candidats: list[dict], n: int, rng: random.Random, exclus: set) -> list[dict]:
    pool = [c for c in candidats if c["numero"] not in exclus
            and LONGUEUR[0] <= len(c["phrase"]) <= LONGUEUR[1]]
    avec = [c for c in pool if annoter(c["phrase"], c["langue"])]
    n_avec = round(n * 0.7)
    choix = rng.sample(avec, n_avec)
    ids = {c["id"] for c in choix}
    # Un seul tirage par article pour diversifier les lots.
    reste = [c for c in pool if c["id"] not in ids]
    choix += rng.sample(reste, n - n_avec)
    return choix


def ecrire_lot(chemin: Path, lot: list[dict], prefixe: str, forcer: bool) -> None:
    if chemin.exists() and not forcer:
        raise FileExistsError(f"{chemin} existe : il contient peut-être des corrections humaines.")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    champs = ["item_id", "langue", "article", "page", "phrase", "entites",
              "entites_lisibles", "statut", "commentaire"]
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for k, c in enumerate(lot, 1):
            e = annoter(c["phrase"], c["langue"])
            w.writerow({"item_id": c.get("item_id") or f"{prefixe}{k:03d}", "langue": c["langue"],
                        "article": c["article"], "page": c["page"], "phrase": c["phrase"],
                        "entites": vers_texte(e), "entites_lisibles": lisible(c["phrase"], e),
                        "statut": "a_verifier", "commentaire": ""})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forcer", action="store_true", help="Réécrire les lots à corriger.")
    args = parser.parse_args()
    rng = random.Random(GRAINE)
    corpus = {"fr": phrases("fr"), "ar": phrases("ar")}

    # Lot FR dev : les 60 phrases historiques.
    dev_fr = []
    for r in lire(RACINE / "data/dev/ner_a_annoter_v1.csv"):
        m = RE_NUM_FR.match(r["article_fr"])
        dev_fr.append({"item_id": r["item_id"], "langue": "fr", "article": r["article_fr"],
                       "numero": int(m.group(1)) if m else None, "page": r["page_fr"],
                       "phrase": r["phrase"]})
    # Un article ne figure que dans un seul lot, toutes langues confondues.
    exclus = {c["numero"] for c in dev_fr}
    lots = {("dev", "fr"): dev_fr}
    for nom, langue in [("test", "fr"), ("dev", "ar"), ("test", "ar")]:
        lot = tirer(corpus[langue], TAILLE_LOT, rng, exclus)
        exclus |= {c["numero"] for c in lot}
        lots[(nom, langue)] = lot
    # L'entraînement d'une langue exclut les articles évalués dans cette langue.
    exclus_langue = {lg: {c["numero"] for (_, l2), lot in lots.items() if l2 == lg for c in lot}
                     for lg in ("fr", "ar")}

    dossier = RACINE / "data/a_annoter"
    for (nom, langue), lot in lots.items():
        prefixe = f"N{nom[0].upper()}{langue.upper()}"
        ecrire_lot(dossier / f"ner_{nom}_{langue}_v1.csv", lot, prefixe, args.forcer)

    resume = {"graine": GRAINE, "articles_exclus_de_l_entrainement": {
        lg: sorted(n for n in s if n) for lg, s in exclus_langue.items()}}
    sortie = RACINE / "data/silver"
    sortie.mkdir(parents=True, exist_ok=True)
    for langue, liste in corpus.items():
        n_phr = n_ent = 0
        with open(sortie / f"ner_silver_{langue}.jsonl", "w", encoding="utf-8") as f:
            for c in liste:
                if c["numero"] in exclus_langue[langue]:
                    continue
                e = annoter(c["phrase"], langue)
                f.write(json.dumps({**c, "entites": e}, ensure_ascii=False) + "\n")
                n_phr += 1
                n_ent += len(e)
        resume[langue] = {"phrases_entrainement": n_phr, "entites_regles": n_ent,
                          "phrases_total": len(liste)}
    with open(sortie / "ner_silver_resume.json", "w", encoding="utf-8") as f:
        json.dump(resume, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in resume.items() if k != "articles_exclus_de_l_entrainement"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
