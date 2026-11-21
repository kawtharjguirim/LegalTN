"""Abstention calibrée (palier Platinum) : le signal d'abstention est-il fiable, et à quel taux d'erreur ?

Signal : cosinus normalisé maximal de la recherche hybride (celui de la démo, ``service.abstenir``).
Évalué sur :
- le **dev** (77 questions : 56 + 21 arabes traduites), seuils réglés dessus : mesure optimiste,
  corrigée par un leave-one-out ;
- les **12 questions de l'étude d'utilité** (``etude_utilite/taches_v1.csv``), écrites après le
  réglage des seuils et absentes du dev : seule mesure non optimiste, mais petite (10 + 2).

Sorties : ``reports/platinum/abstention/`` (``calibration.json``, ``points.csv``, ``RESULTATS.md`` écrit à la main).

Usage : python -X utf8 -m src.platinum.calibration [--appareil cpu]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np

from src.rag import service
from src.rag.evaluer import questions, seuil_loo
from src.rag.recherche import RACINE, Recherche

ETUDE = RACINE / "etude_utilite/taches_v1.csv"


def base(ref: str) -> str:
    """Numéro de base d'un article (« 63-2 » et « 376 bis » -> « 63 » et « 376 »)."""
    return ref.replace("FR-", "").replace("AR-", "").split()[0].split("-")[0].strip()


def auroc(scores: np.ndarray, dans: np.ndarray) -> float:
    """Probabilité qu'une question du périmètre ait un signal plus élevé qu'une hors périmètre."""
    pos, neg = scores[dans], scores[~dans]
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))


def risque_couverture(scores: np.ndarray, correct: np.ndarray) -> list[dict]:
    """Courbe risque–couverture : on répond aux questions dont le signal dépasse un seuil ;
    risque = part de réponses fausses (ou hors périmètre) parmi celles données."""
    ordre = np.argsort(-scores)
    points = []
    for n in range(1, len(scores) + 1):
        pris = ordre[:n]
        points.append({"couverture": round(n / len(scores), 3), "seuil": round(float(scores[ordre[n - 1]]), 4),
                       "risque": round(float(1 - correct[pris].mean()), 3)})
    return points


def aire_risque(points: list[dict]) -> float:
    return round(float(np.mean([p["risque"] for p in points])), 4)


def ic_bootstrap(valeurs: np.ndarray, n: int = 5000, graine: int = 20261121) -> list[float]:
    rng = random.Random(graine)
    m = sorted(float(np.mean(rng.choices(list(valeurs), k=len(valeurs)))) for _ in range(n))
    return [round(m[int(0.025 * n)], 3), round(m[int(0.975 * n) - 1], 3)]


def charger_etude() -> list[dict]:
    with open(ETUDE, encoding="utf-8-sig", newline="") as f:
        return [{"id": r["id"], "langue": "fr", "dans": r["dans_perimetre"] == "oui", "question": r["enonce"],
                 "reference": r["article_reference"]} for r in csv.DictReader(f)]


def interroger(moteur: Recherche, qs: list[dict]) -> None:
    for q in qs:
        res, sig = moteur.rechercher(q["question"], "hybride", False, k=3)
        langue = "ar" if sig["langue"] == "ar" else "fr"
        q.update({"cos": sig["cos_max"], "cosnorm": sig["cosnorm_max"], "ecriture": langue,
                  "top1": res[0].article if res else "", "abstient": service.abstenir(sig, langue)})
        q["bon_top1"] = bool(q["dans"] and base(q["top1"]) == base(q["reference"])) if q["dans"] else False


def mesurer(qs: list[dict]) -> dict:
    dans = np.array([q["dans"] for q in qs])
    abst = np.array([q["abstient"] for q in qs])
    bon = np.array([q["bon_top1"] for q in qs])
    repond = ~abst
    correct = (dans & bon & repond) | (~dans & abst)          # décision juste de bout en bout
    return {
        "n": len(qs), "n_dans": int(dans.sum()), "n_hors": int((~dans).sum()),
        "fausses_abstentions": int((dans & abst).sum()),
        "hors_perimetre_repondu": int((~dans & repond).sum()),
        "reponses_donnees": int(repond.sum()),
        "bon_article_parmi_reponses_dans_perimetre": int((dans & bon & repond).sum()),
        "decision_juste": round(float(correct.mean()), 3), "ic95_decision_juste": ic_bootstrap(correct.astype(float)),
        "reponse_fausse_ou_hors_parmi_donnees": round(float(1 - correct[repond].mean()), 3) if repond.any() else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/abstention")
    parser.add_argument("--appareil", default="cpu")
    args = parser.parse_args()
    moteur = Recherche("intfloat/multilingual-e5-base", appareil=args.appareil)
    dev, etude = questions(), charger_etude()
    for q in dev:
        q["reference"] = q["reference"].removeprefix("FR-")
    interroger(moteur, dev)
    interroger(moteur, etude)

    res = {"regle": {"signal": service.SIGNAL, "seuils": service.SEUILS, "seuil_brut_ar": service.SEUILS_BRUT}}
    res["dev"] = mesurer(dev)
    res["etude_12_questions_neuves"] = mesurer(etude)

    # Pouvoir discriminant du signal et fiabilité par écriture (dev).
    dans = np.array([q["dans"] for q in dev])
    cosn = np.array([q["cosnorm"] for q in dev])
    ecr = np.array([q["ecriture"] for q in dev])
    res["auroc_dev"] = {"global": round(auroc(cosn, dans), 3)} | {
        g: round(auroc(cosn[ecr == g], dans[ecr == g]), 3) for g in ("fr", "ar") if (ecr == g).sum() and dans[ecr == g].any() and (~dans[ecr == g]).any()}
    # Leave-one-out : seuil réglé sans la question, par écriture.
    loo = np.zeros(len(dev), dtype=bool)
    for g in ("fr", "ar"):
        idx = np.flatnonzero(ecr == g)
        loo[idx], _ = seuil_loo(cosn[idx], dans[idx])
    for q, a in zip(dev, loo):
        q["abstient_loo"] = bool(a)
    bon = np.array([q["bon_top1"] for q in dev])
    corr_loo = (dans & bon & ~loo) | (~dans & loo)
    res["dev_leave_one_out"] = {"decision_juste": round(float(corr_loo.mean()), 3), "ic95": ic_bootstrap(corr_loo.astype(float)),
                                "fausses_abstentions": int((dans & loo).sum()), "hors_perimetre_repondu": int((~dans & ~loo).sum())}
    # Courbe risque–couverture : « bonne réponse » = dans le périmètre avec le bon article en tête.
    correct_rc = dans & bon
    pts = risque_couverture(cosn, correct_rc)
    res["risque_couverture"] = {"aire_risque": aire_risque(pts),
                                "risque_sans_abstention": round(float(1 - correct_rc.mean()), 3),
                                "points_cles": [min(pts, key=lambda p: abs(p["couverture"] - c)) for c in (0.25, 0.5, 0.75, 1.0)]}

    args.sortie.mkdir(parents=True, exist_ok=True)
    with open(args.sortie / "calibration.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    with open(args.sortie / "points.csv", "w", encoding="utf-8-sig", newline="") as f:
        champs = ["jeu", "id", "langue", "dans", "question", "reference", "top1", "cos", "cosnorm", "abstient", "bon_top1"]
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        for jeu, qs in (("dev", dev), ("etude", etude)):
            for q in qs:
                w.writerow({"jeu": jeu, **q})
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
