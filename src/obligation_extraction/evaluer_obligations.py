"""Évaluation des extractions d'obligations contre un modèle annoté.

Compare un CSV de prédictions (``extraire_obligations.py``) au modèle
``obligations_modele_v1.csv`` rempli à la main. Refuse de calculer quoi que
ce soit si le modèle ne contient aucune annotation : un champ ``modal``
vide n'est **pas** une annotation négative.

Métriques : précision/rappel/F1 par modal (obligation, interdiction,
permission), détection binaire obligation/non-obligation, exactitude de
``qui`` et ``quand``. Sortie JSON + éventuel CSV des erreurs.
"""

from __future__ import annotations

import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path


def _lire_csv(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def annotations_disponibles(gold: list[dict]) -> list[dict]:
    """Lignes réellement annotées : ``modal`` renseigné ou ``non_obligation``
    dans le commentaire. Les autres lignes sont ignorées, pas traitées comme
    des négatifs."""
    return [
        g for g in gold
        if g.get("modal", "").strip()
        or "non_obligation" in g.get("commentaire", "").lower()
    ]


CLASSES_ROLE = ("employeur", "salarie", "apprenti", "maitre", "administration", "juridiction",
                "organisation", "parties", "toute_personne", "autre", "aucun")
# Ordre = priorité : une expression longue (« le conseil de prud'hommes ») doit être reconnue
# avant ses mots les plus courants (« conseil », « entreprise »).
_MOTS_ROLE = (
    ("juridiction", ("tribunal", "juge", "greffier", "prud'hom", "arbitrage", "juridiction", "magistrat")),
    ("organisation", ("syndicat", "commission", "groupement", "union", "delegue", "representant",
                      "organisation", "conseil", "bureau", "comite", "association")),
    ("apprenti", ("apprenti",)),
    ("maitre", ("maitre",)),
    ("administration", ("ministre", "secretaire d'etat", "inspect", "agent", "gouverneur", "controleur",
                        "caisse", "service", "direction generale", "administration", "autorite", "decret", "arrete")),
    ("employeur", ("employeur", "chef d'entreprise", "chef d'etablissement", "entrepreneur", "entreprise",
                   "etablissement", "patron", "proprietaire", "gerant", "directeur", "adjudicataire")),
    ("salarie", ("salarie", "travailleur", "ouvrier", "employe", "personnel", "enfant", "femme", "adolescent")),
    ("parties", ("partie",)),
    ("toute_personne", ("toute personne", "nul", "aucun", "chacun", "quiconque")),
)


def classe_role(texte: str) -> str:
    """Classe de rôle d'un ``qui`` (écrit tel que dans la phrase), pour comparer annotation et prédiction.

    Vide = ``aucun`` (rôle non nommé : voix passive, sujet implicite). Sans mot reconnu = ``autre``."""
    t = " ".join(texte.replace("’", "'").split()).lower().strip()
    if not t:
        return "aucun"
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    for classe, mots in _MOTS_ROLE:
        if any(m in t for m in mots):
            return classe
    return "autre"


def _prf(vp: int, fp: int, fn: int) -> dict:
    p = vp / (vp + fp) if vp + fp else 0.0
    r = vp / (vp + fn) if vp + fn else 0.0
    return {
        "precision": round(p, 4), "rappel": round(r, 4),
        "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0,
        "vp": vp, "fp": fp, "fn": fn,
    }


def evaluer(gold: list[dict], predictions: list[dict]) -> dict:
    refs = {g["obligation_id"]: g for g in gold}
    preds = {p["obligation_id"]: p for p in predictions}
    ids = sorted(set(refs) & set(preds))
    if not ids:
        raise ValueError("aucun identifiant commun entre gold et prédictions")

    compte = Counter()
    erreurs = []
    qui_ok = quand_ok = nb_qui = nb_quand = 0
    for i in ids:
        g, p = refs[i], preds[i]
        g_obl = "non_obligation" not in g.get("commentaire", "").lower()
        p_obl = p.get("est_obligation_predite", "False").lower() == "true"
        compte[("detection", g_obl, p_obl)] += 1
        if g_obl and p_obl:
            compte[("modal", g["modal"].strip(), p["modal_predit"])] += 1
            compte[("role", classe_role(g.get("qui", "")), classe_role(p.get("qui_predit", "")))] += 1
            if g.get("qui", "").strip():
                nb_qui += 1
                qui_ok += p["qui_predit"].strip().lower() == g["qui"].strip().lower()
            if g.get("quand", "").strip():
                nb_quand += 1
                quand_ok += p["quand_predit"].strip().lower() == g["quand"].strip().lower()
        if (g_obl != p_obl) or (g_obl and p_obl
                                and g["modal"].strip() != p["modal_predit"]):
            erreurs.append({
                "obligation_id": i, "article_fr": g["article_fr"],
                "phrase": g["phrase"],
                "modal_gold": g.get("modal", ""), "modal_predit": p["modal_predit"],
                "obligation_gold": g_obl, "obligation_predite": p_obl,
            })

    vp_d = compte[("detection", True, True)]
    fp_d = compte[("detection", False, True)]
    fn_d = compte[("detection", True, False)]
    resultats = {
        "n_commun": len(ids),
        "detection_obligation": _prf(vp_d, fp_d, fn_d),
        "modal_par_classe": {},
        "qui_exactitude": round(qui_ok / nb_qui, 4) if nb_qui else None,
        "quand_exactitude": round(quand_ok / nb_quand, 4) if nb_quand else None,
        "n_erreurs": len(erreurs),
    }
    for modal in ("obligation", "interdiction", "permission"):
        vp = compte[("modal", modal, modal)]
        fp = sum(v for (k, gm, pm), v in compte.items()
                 if k == "modal" and pm == modal and gm != modal)
        fn = sum(v for (k, gm, pm), v in compte.items()
                 if k == "modal" and gm == modal and pm != modal)
        resultats["modal_par_classe"][modal] = _prf(vp, fp, fn)

    # F1 par rôle : classes de rôle (employeur, salarié, administration…), sur les phrases que le gold
    # et l'extracteur retiennent toutes deux comme obligations. « aucun » = rôle non nommé.
    resultats["role_par_classe"] = {}
    for classe in CLASSES_ROLE:
        vp = compte[("role", classe, classe)]
        fp = sum(v for (k, gc, pc), v in compte.items() if k == "role" and pc == classe and gc != classe)
        fn = sum(v for (k, gc, pc), v in compte.items() if k == "role" and gc == classe and pc != classe)
        if vp + fp + fn:
            resultats["role_par_classe"][classe] = _prf(vp, fp, fn) | {"support_gold": vp + fn}
    total_role = sum(v for (k, _, _), v in compte.items() if k == "role")
    juste = sum(v for (k, gc, pc), v in compte.items() if k == "role" and gc == pc)
    resultats["role_exactitude_classes"] = round(juste / total_role, 4) if total_role else None
    f1s = [c["f1"] for c in resultats["role_par_classe"].values() if c["support_gold"]]
    resultats["role_macro_f1"] = round(sum(f1s) / len(f1s), 4) if f1s else None
    nommes = [c for n, c in resultats["role_par_classe"].items() if n != "aucun" and c["support_gold"]]
    resultats["role_macro_f1_roles_nommes"] = round(sum(c["f1"] for c in nommes) / len(nommes), 4) if nommes else None
    return {"resultats": resultats, "erreurs": erreurs}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path,
                        default=Path("data/dev/obligations_modele_v1.csv"))
    parser.add_argument("--predictions", type=Path,
                        default=Path("data/dev/obligations_predictions_dev_v1.csv"))
    parser.add_argument("--sortie", type=Path,
                        default=Path("reports/reprise/evaluation_obligations.json"))
    parser.add_argument("--erreurs", type=Path, default=None)
    args = parser.parse_args(argv)

    gold = _lire_csv(args.gold)
    annotees = annotations_disponibles(gold)
    if not annotees:
        print(
            "Aucune annotation dans le modèle : évaluation impossible sans "
            "gold humain. Aucun score produit.", file=sys.stderr,
        )
        return 2

    predictions = _lire_csv(args.predictions)
    bilan = evaluer(annotees, predictions)
    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(args.sortie, "w", encoding="utf-8") as f:
        json.dump(bilan["resultats"], f, ensure_ascii=False, indent=2)
    if args.erreurs:
        with open(args.erreurs, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(bilan["erreurs"][0])) if bilan[
                "erreurs"] else csv.DictWriter(f, fieldnames=["obligation_id"])
            w.writeheader()
            w.writerows(bilan["erreurs"])
    print(json.dumps(bilan["resultats"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
