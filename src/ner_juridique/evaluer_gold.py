"""Évaluation NER sur le gold dev corrigé à la main (lignes ``statut = verifie``), sans
réentraîner les encodeurs.

Systèmes : règles ; CRF du Bronze (réentraîné en quelques secondes, 3 graines) ; modèles
fine-tunés sauvegardés dans ``models/ner/`` (graine 13 : XLM-R pour le FR, AraBERT pour l'AR).
Le tableau sur 3 graines de tous les encodeurs demande de relancer ``entrainer`` (≈ 45 min).

Sorties dans --sortie : ``gold_dev_<langue>.json`` (F1 par type) et
``erreurs_gold_dev_<langue>.csv`` (chaque erreur catégorisée : frontière, type, oubli, faux
positif), pour l'analyse d'erreurs.

Usage : python -X utf8 -m src.ner_juridique.evaluer_gold --langue fr
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .donnees import RACINE, charger_lot, charger_silver, f1_chevauchement, f1_spans, separer_validation
from .entrainer import GRAINES, entrainer_crf, predire_crf, predire_encodeur
from .regles import annoter

MODELES = {"fr": "fr_xlmr", "ar": "ar_arabert"}


def categoriser(gold: list, pred: list, phrase: str) -> list[dict]:
    """Erreurs d'une phrase : frontière (chevauche, même type), type (mêmes bornes ou
    chevauchement d'un autre type), oubli (rien de prédit), faux positif (rien en gold)."""
    sg, sp = set(map(tuple, gold)), set(map(tuple, pred))
    erreurs = []
    for g in sorted(sg - sp):
        voisins = [p for p in sp - sg if p[0] < g[1] and g[0] < p[1]]
        if not voisins:
            cat, p = "oubli", None
        else:
            p = voisins[0]
            cat = "frontiere" if p[2] == g[2] else "type"
        erreurs.append({"categorie": cat, "gold": f"{phrase[g[0]:g[1]]} / {g[2]}",
                        "prediction": f"{phrase[p[0]:p[1]]} / {p[2]}" if p else ""})
    for p in sorted(sp - sg):
        if not any(g[0] < p[1] and p[0] < g[1] for g in sg):
            erreurs.append({"categorie": "faux_positif", "gold": "",
                            "prediction": f"{phrase[p[0]:p[1]]} / {p[2]}"})
    return erreurs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--langue", choices=["fr", "ar"], required=True)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/silver/ner")
    parser.add_argument("--accepter-claude", action="store_true",
                        help="Accepter aussi les phrases annotées par Claude (verifie_claude) : "
                             "pré-gold, pas un gold humain.")
    args = parser.parse_args()

    statuts = ("verifie", "verifie_claude") if args.accepter_claude else ("verifie",)
    gold, chemin = charger_lot("dev", args.langue, statuts=statuts)
    if not gold:
        raise SystemExit(f"Aucune ligne {statuts} dans {chemin} : corriger le lot d'abord "
                         "(outils/annotateur_ner.html).")
    n_humain = sum(g["statut"] == "verifie" for g in gold)
    nature = ("gold humain" if n_humain == len(gold) else "pré-gold Claude" if n_humain == 0
              else f"mixte : {n_humain} phrases relues par un humain, {len(gold) - n_humain} par Claude")
    print(f"Référence : {len(gold)} phrases ({chemin.name}), {sum(len(g['entites']) for g in gold)} "
          f"entités — {nature}")
    references = [g["entites"] for g in gold]
    predictions = {"regles": [[tuple(e) for e in annoter(g["phrase"], args.langue)] for g in gold]}

    silver = charger_silver(args.langue)
    crf_f1 = []
    for graine in GRAINES:
        train, _ = separer_validation(silver, graine=graine)
        pred = predire_crf(entrainer_crf(train), gold)
        crf_f1.append(f1_spans(references, pred))
        if graine == GRAINES[0]:
            predictions["crf"] = pred

    dossier = RACINE / "models/ner" / MODELES[args.langue]
    if dossier.exists():
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(dossier)
        modele = AutoModelForTokenClassification.from_pretrained(dossier)
        if torch.cuda.is_available():
            modele = modele.to("cuda")
        predictions[MODELES[args.langue]] = predire_encodeur(modele, tok, gold)
    else:
        print(f"Modèle absent : {dossier} (entrainer --sauver models/ner)")

    resultats = {"langue": args.langue, "fichier_gold": chemin.name, "nature_reference": nature,
                 "n_phrases_relues_humain": n_humain, "n_phrases": len(gold),
                 "n_entites": sum(len(r) for r in references), "systemes": {}}
    lignes_erreurs = []
    for nom, pred in predictions.items():
        m = f1_spans(references, pred)
        m["souple"] = f1_chevauchement(references, pred)
        resultats["systemes"][nom] = m
        for g, r, p in zip(gold, references, pred):
            for e in categoriser(r, p, g["phrase"]):
                lignes_erreurs.append({"systeme": nom, "id": g["id"], **e, "phrase": g["phrase"]})
    resultats["crf_3_graines_f1_micro"] = [round(m["micro"]["f1"], 4) for m in crf_f1]

    args.sortie.mkdir(parents=True, exist_ok=True)
    prefixe = "gold" if n_humain == len(gold) else "pregold"
    with open(args.sortie / f"{prefixe}_dev_{args.langue}.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    with open(args.sortie / f"erreurs_{prefixe}_dev_{args.langue}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["systeme", "id", "categorie", "gold", "prediction", "phrase"])
        w.writeheader()
        w.writerows(lignes_erreurs)

    print(f"\n{'Système':12s} {'P':>6s} {'R':>6s} {'F1':>6s}  macro  | ROLE  INST  DELAI MONT.")
    for nom, m in resultats["systemes"].items():
        t = m["par_type"]
        print(f"{nom:12s} {m['micro']['precision']:6.3f} {m['micro']['rappel']:6.3f} {m['micro']['f1']:6.3f}"
              f"  {m['macro_f1']:.3f}  | " + " ".join(f"{t[x]['f1']:.2f}" for x in
                                                   ("ROLE", "INSTITUTION", "DELAI", "MONTANT"))
              + f" | {m['souple']['f1']:.3f}")
    print(f"CRF sur 3 graines (F1 micro) : {resultats['crf_3_graines_f1_micro']}")
    compte = {}
    for e in lignes_erreurs:
        compte.setdefault(e["systeme"], {}).setdefault(e["categorie"], 0)
        compte[e["systeme"]][e["categorie"]] += 1
    print("Erreurs par catégorie :", json.dumps(compte, ensure_ascii=False))


if __name__ == "__main__":
    main()
