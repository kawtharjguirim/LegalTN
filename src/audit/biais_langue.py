"""Biais de langue : la même question, posée en français ou en arabe, retrouve-t-elle le même article ?

Mesure sur les 21 paires question française / traduction arabe du dev (traductions par Claude, à valider) la
recherche hybride (BM25 + e5) avec fusion bilingue pondérée : le classement dense de l'**autre** langue entre dans la
fusion RRF avec le poids ``poids_autre`` (0 = ignoré, 1 = à égalité). On regarde si l'écart entre langues se réduit
sans dégrader le français.

Variante « pivot » (``--pivot``) : la question arabe est d'abord traduite en français par le LLM local, puis cherchée
dans le corpus français ; le LLM n'est appelé que pour la traduction (résultats mis en cache).

Usage : python -X utf8 -m src.audit.biais_langue [--appareil cpu] [--pivot --modele-traduction qwen2.5:7b]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.rag import generer

from src.platinum.calibration import base
from src.rag.recherche import RACINE, Recherche

POIDS = (0.0, 0.25, 0.5, 1.0)
CACHE_PIVOT = RACINE / "runs/cache_traductions_ar_fr.json"
CONSIGNE_PIVOT = ("Tu traduis une question juridique écrite en arabe standard vers le français, avec le vocabulaire du "
                  "Code du travail tunisien. Réponds uniquement par la traduction, sur une seule ligne.")


def traduire_ar_fr(question: str, modele: str) -> str:
    try:
        cache = json.loads(CACHE_PIVOT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    cle = f"{modele}|{question}"
    if cle not in cache:
        texte = generer.appeler([{"role": "system", "content": CONSIGNE_PIVOT}, {"role": "user", "content": question}], modele)
        cache[cle] = texte.strip().strip('"«» ').split("\n")[0]
        CACHE_PIVOT.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PIVOT.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[cle]


def evaluer_pivot(moteur: Recherche, ps: list[dict], modele: str) -> dict:
    """Question arabe -> traduction française -> recherche monolingue française."""
    lignes = []
    for p in ps:
        trad = traduire_ar_fr(p["ar"], modele)
        r, _ = moteur.rechercher(trad, "hybride", False, k=5)
        ref = base(p["reference"])
        tops = [base(x.article) for x in r]
        lignes.append({"id": p["id"], "ar1": tops[:1] == [ref], "ar5": ref in tops, "traduction": trad})
    n = len(lignes)
    return {"modele_traduction": modele, "r_at_1_ar": round(sum(l["ar1"] for l in lignes) / n, 3), "r_at_5_ar": round(sum(l["ar5"] for l in lignes) / n, 3),
            "exemples": [{"id": l["id"], "juste": l["ar1"], "traduction": l["traduction"]} for l in lignes[:21]]}


def paires() -> list[dict]:
    fr = {x["id"]: x for x in csv.DictReader(open(RACINE / "data/dev/questions_dev_v2.csv", encoding="utf-8-sig"))}
    out = []
    for a in csv.DictReader(open(RACINE / "data/dev/questions_dev_ar_traduites_v1.csv", encoding="utf-8-sig")):
        f = fr[a["source_id"]]
        out.append({"id": f["id"], "fr": f["question"], "ar": a["question"], "reference": f["article_reference"].strip().removesuffix(".0")})
    return out


def evaluer(appareil: str, pivot: str | None = None) -> dict:
    moteur = Recherche("intfloat/multilingual-e5-base", appareil=appareil)
    ps = paires()
    res = {"n_paires": len(ps), "configurations": {}}
    configs = [("monolingue", dict(bilingue=False))] + [(f"bilingue_poids_{w}", dict(bilingue=True, poids_autre=w)) for w in POIDS]
    for nom, kw in configs:
        lignes = []
        for p in ps:
            top = {}
            for lg in ("fr", "ar"):
                r, _ = moteur.rechercher(p[lg], "hybride", k=5, **kw)
                top[lg] = [base(x.article) for x in r]
            ref = base(p["reference"])
            lignes.append({"id": p["id"], "fr1": top["fr"][:1] == [ref], "ar1": top["ar"][:1] == [ref], "fr5": ref in top["fr"], "ar5": ref in top["ar"],
                           "meme_top1": top["fr"][:1] == top["ar"][:1]})
        n = len(lignes)
        res["configurations"][nom] = {
            "r_at_1_fr": round(sum(l["fr1"] for l in lignes) / n, 3), "r_at_1_ar": round(sum(l["ar1"] for l in lignes) / n, 3),
            "r_at_5_fr": round(sum(l["fr5"] for l in lignes) / n, 3), "r_at_5_ar": round(sum(l["ar5"] for l in lignes) / n, 3),
            "juste_les_deux": sum(l["fr1"] and l["ar1"] for l in lignes), "fr_seulement": sum(l["fr1"] and not l["ar1"] for l in lignes),
            "ar_seulement": sum(l["ar1"] and not l["fr1"] for l in lignes), "meme_premier_article": round(sum(l["meme_top1"] for l in lignes) / n, 3),
            "ecart_r_at_1": round(sum(l["fr1"] for l in lignes) / n - sum(l["ar1"] for l in lignes) / n, 3)}
        print(nom, res["configurations"][nom], flush=True)
    if pivot:
        res["pivot_traduction"] = evaluer_pivot(moteur, ps, pivot)
        print("pivot", {k: v for k, v in res["pivot_traduction"].items() if k != "exemples"}, flush=True)
    return res


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appareil", default="cpu")
    parser.add_argument("--pivot", action="store_true")
    parser.add_argument("--modele-traduction", default="qwen2.5:7b")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/biais_langue")
    args = parser.parse_args()
    res = evaluer(args.appareil, args.modele_traduction if args.pivot else None)
    args.sortie.mkdir(parents=True, exist_ok=True)
    (args.sortie / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
