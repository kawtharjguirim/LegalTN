"""Questions en tunisien (arabizi) : comparaison de cinq méthodes de recherche (palier Gold).

Question de recherche du cahier des charges : la recherche après traduction de la question
bat-elle la recherche multilingue directe pour des questions tunisiennes ?

Méthodes :
- A ``directe_fr``         : la question telle quelle, recherche hybride sur le corpus français ;
- B ``multilingue``        : la question telle quelle, recherche dense e5 sur les deux corpus ;
- C ``translit_ar``        : translittération par règles, recherche hybride sur le corpus arabe ;
- D ``traduction_fr``      : traduction par qwen2.5:3b vers le français, recherche hybride FR ;
- E ``traduction_ar``      : traduction par qwen2.5:3b vers l'arabe standard, recherche hybride AR.

Jeux : ``questions_tun_v1.csv`` (24 dans le périmètre + 6 hors, rédigées par Claude, à valider)
et les questions tunisiennes de ``questions_dev_v2.csv`` (6 + 3, déjà consultées).
Mesures : R@1, R@5, MRR ; abstention avec la règle de la démo (``service.abstenir``).

Usage : python -X utf8 -m src.tunisien.evaluer --sortie reports/gold/tunisien
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.rag.recherche import RACINE, Recherche, repondre
from src.rag.service import abstenir

from .arabizi import translitterer
from .traduction import traduire

METHODES = ["directe_fr", "multilingue", "translit_ar", "traduction_fr", "traduction_ar"]
MODELE_TRADUCTION = "qwen2.5:3b"


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def jeu() -> list[dict]:
    lignes = [{**q, "jeu": "tun_v1"} for q in lire(RACINE / "data/dev/questions_tun_v1.csv")]
    lignes += [{**q, "jeu": "dev_v2"} for q in lire(RACINE / "data/dev/questions_dev_v2.csv")
               if q["langue"] == "tun"]
    for q in lignes:
        q["dans"] = q["type"] == "dans_perimetre"
        q["reference"] = (q["article_reference"] or "").strip().removesuffix(".0")
    return lignes


def requete(methode: str, question: str) -> tuple[str, str, bool, str]:
    """(texte cherché, langue du corpus, bilingue, mode)."""
    if methode == "directe_fr":
        return question, "fr", False, "hybride"
    if methode == "multilingue":
        return question, "fr", True, "dense"
    if methode == "translit_ar":
        return translitterer(question), "ar", False, "hybride"
    if methode == "traduction_fr":
        return traduire(question, "fr", MODELE_TRADUCTION), "fr", False, "hybride"
    return traduire(question, "ar", MODELE_TRADUCTION), "ar", False, "hybride"


def resumer(lignes: list[dict]) -> dict:
    dans = [l for l in lignes if l["dans"]]
    hors = [l for l in lignes if not l["dans"]]
    rangs = [l["rang"] for l in dans]
    return {
        "n_dans": len(dans), "n_hors": len(hors),
        "r_at_1": round(sum(r == 1 for r in rangs) / len(dans), 3) if dans else None,
        "r_at_5": round(sum(r <= 5 for r in rangs) / len(dans), 3) if dans else None,
        "mrr": round(sum(1 / r for r in rangs if r < 99) / len(dans), 3) if dans else None,
        "fausse_abstention": round(sum(l["abstention"] for l in dans) / len(dans), 3) if dans else None,
        "repond_et_juste": round(sum((not l["abstention"]) and l["rang"] == 1 for l in dans) / len(dans), 3) if dans else None,
        "hors_refuse": round(sum(l["abstention"] for l in hors) / len(hors), 3) if hors else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/tunisien")
    parser.add_argument("--appareil", default="cpu")
    parser.add_argument("--modele-traduction", default="qwen2.5:3b")
    parser.add_argument("--methodes", nargs="+", default=METHODES)
    args = parser.parse_args()
    global MODELE_TRADUCTION
    MODELE_TRADUCTION = args.modele_traduction
    moteur = Recherche("intfloat/multilingual-e5-base", appareil=args.appareil)
    questions = jeu()
    details, resultats = [], {}
    for methode in args.methodes:
        lignes = []
        for q in questions:
            texte, langue, bilingue, mode = requete(methode, q["question"])
            res, sig = moteur.rechercher(texte, mode, bilingue, k=50) if texte.strip() else ([], {})
            labels = [r.article for r in res]
            rang = labels.index(q["reference"]) + 1 if q["reference"] in labels else 99
            # Abstention : règle de la démo, dans la langue du texte réellement cherché.
            lg = repondre.detecter_langue(texte) if texte else langue
            abst = (not res) or abstenir(sig, lg)
            lignes.append({**q, "methode": methode, "texte_cherche": texte, "rang": rang,
                           "top3": " | ".join(labels[:3]), "abstention": abst,
                           "cos_max": round(sig.get("cos_max", 0.0), 4),
                           "cosnorm_max": round(sig.get("cosnorm_max", 0.0), 4)})
        resultats[methode] = {"global": resumer(lignes),
                              "par_jeu": {j: resumer([l for l in lignes if l["jeu"] == j])
                                          for j in ("tun_v1", "dev_v2")}}
        g = resultats[methode]["global"]
        print(f"{methode:14s} R@1 {g['r_at_1']}  R@5 {g['r_at_5']}  MRR {g['mrr']}  "
              f"fausse abst. {g['fausse_abstention']}  répond juste {g['repond_et_juste']}  "
              f"hors refusé {g['hors_refuse']}", flush=True)
        details += lignes
    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "tunisien_resultats.json", "w", encoding="utf-8") as f:
        json.dump({"n_questions": len(questions), "modele_traduction": MODELE_TRADUCTION, "methodes": resultats,
                   "avertissement": "questions tun_v1 rédigées par Claude, à valider par une locutrice native ; "
                                    "dev_v2 déjà consulté ; abstention réglée pour FR/AR, pas pour le tunisien"},
                  f, ensure_ascii=False, indent=2)
    with open(args.sortie / "tunisien_details.csv", "w", encoding="utf-8-sig", newline="") as f:
        champs = ["methode", "jeu", "id", "dans", "reference", "question", "texte_cherche", "rang",
                  "top3", "abstention", "cos_max", "cosnorm_max"]
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(details)


if __name__ == "__main__":
    main()
