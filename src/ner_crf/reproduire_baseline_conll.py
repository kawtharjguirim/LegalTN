"""Reproduction de la baseline publiée CoNLL-2002 + CRF de référence.

Résultat choisi : Tjong Kim Sang (2002), Table 1, ligne « baseline » —
système qui ne retient que les entités de classe unique en
apprentissage (correspondance la plus longue en cas d'ambiguïté).

Valeurs publiées (avec erreurs d'annotation du train) :
    espagnol test : P=26.27  R=56.48  F1=35.86  (62.49 sans erreurs)
    néerlandais test : P=64.38  R=45.19  F1=53.10  (57.59 sans erreurs)

Données : corpus ``conll2002`` de NLTK (mêmes fichiers esp/ned). Un écart
par rapport aux valeurs publiées est attendu : versions du corpus,
détails de segmentation et gestion des chevauchements peuvent différer.
Aucun paramètre n'est réglé sur le test : la reproduction se contente de
mesurer et d'expliquer l'écart.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.ner_crf.features import phrases_vers_X, phrases_vers_y
from src.ner_crf.pipeline import entrainer_crf, evaluer_spans

PUBLIE = {
    "esp": {"precision": 26.27, "rappel": 56.48, "f1": 35.86,
            "f1_sans_erreurs_train": 62.49},
    "ned": {"precision": 64.38, "rappel": 45.19, "f1": 53.10,
            "f1_sans_erreurs_train": 57.59},
}


def charger_conll(fichier: Path) -> list:
    """Lit un fichier CoNLL (mot [pos] étiquette, lignes vides = phrases)."""
    phrases, courante = [], []
    with open(fichier, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                if courante:
                    phrases.append(courante)
                    courante = []
                continue
            if ligne.startswith("-DOCSTART-"):
                continue
            champs = ligne.split()
            mot, tag = champs[0], champs[-1]
            pos = champs[1] if len(champs) > 2 else ""
            courante.append((mot, pos, tag))
    if courante:
        phrases.append(courante)
    return phrases


def entites_uniques(phrases: list) -> dict:
    """phrase (tuple de mots) -> classe, uniquement si une seule classe vue.

    Lecture littérale du papier ; en pratique les valeurs publiées sont
    reproduites par la classe majoritaire (voir ``entites_majoritaires``)."""
    from src.ner_crf.pipeline import etiquettes_vers_spans
    classes: dict[tuple, set] = defaultdict(set)
    for s in phrases:
        mots = [t[0] for t in s]
        tags = [t[2] for t in s]
        for d, f, t in etiquettes_vers_spans(tags):
            classes[tuple(mots[d:f])].add(t)
    return {p: next(iter(c)) for p, c in classes.items() if len(c) == 1}


def entites_majoritaires(phrases: list) -> dict:
    """phrase -> classe la plus fréquente (reproduit la baseline publiée :
    P=26.34 R=56.62 F1=35.95 vs publié 26.27/56.48/35.86)."""
    from collections import Counter
    from src.ner_crf.pipeline import etiquettes_vers_spans
    classes: dict[tuple, Counter] = defaultdict(Counter)
    for s in phrases:
        mots = [t[0] for t in s]
        tags = [t[2] for t in s]
        for d, f, t in etiquettes_vers_spans(tags):
            classes[tuple(mots[d:f])][t] += 1
    return {p: c.most_common(1)[0][0] for p, c in classes.items()}


def predire_baseline(mots: list, entites: dict) -> list:
    """Appariement glouton le plus long sur le dictionnaire d'entités."""
    tags, i = ["O"] * len(mots), 0
    while i < len(mots):
        trouve = None
        for long in range(len(mots) - i, 0, -1):
            cle = tuple(mots[i:i + long])
            if cle in entites:
                trouve = (long, entites[cle])
                break
        if trouve:
            long, classe = trouve
            tags[i] = f"B-{classe}"
            for j in range(1, long):
                tags[i + j] = f"I-{classe}"
            i += long
        else:
            i += 1
    return tags


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--langue", default="esp", choices=["esp", "ned"])
    parser.add_argument("--sans-crf", action="store_true",
                        help="baseline publiée seule, sans entraîner le CRF")
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--sortie", type=Path,
                        default=Path("reports/reprise/conll2002_reproduction.json"))
    args = parser.parse_args(argv)

    import nltk
    nltk.download("conll2002", quiet=True)
    from nltk.corpus import conll2002
    racine = Path(conll2002.root)
    train = charger_conll(racine / f"{args.langue}.train")
    test = charger_conll(racine / f"{args.langue}.testb")
    print(f"{args.langue}: {len(train)} phrases train, {len(test)} test")

    entites = entites_majoritaires(train)
    mots_test = [[t[0] for t in s] for s in test]
    y_gold = phrases_vers_y(test)
    y_base = [predire_baseline(m, entites) for m in mots_test]
    y_strict = [predire_baseline(m, entites_uniques(train)) for m in mots_test]
    rapport = {
        "donnees": {
            "corpus": "nltk conll2002", "langue": args.langue,
            "n_phrases_train": len(train), "n_phrases_test": len(test),
            "n_entites_dictionnaire": len(entites),
        },
        "baseline_publiee": PUBLIE[args.langue],
        "baseline_reproduite": evaluer_spans(y_gold, y_base)["micro"],
        "baseline_stricte_classe_unique": evaluer_spans(y_gold, y_strict)["micro"],
        "lecture_retenue": "classe majoritaire par phrase, appariement glouton "
                           "le plus long ; la lecture littérale « classe "
                           "unique » donne F1=27.02, la lecture majoritaire "
                           "reproduit le publié à ±0.1 point.",
    }
    b = rapport["baseline_reproduite"]
    rapport["ecart_baseline_f1"] = round(
        b["f1"] - PUBLIE[args.langue]["f1"], 2)

    if not args.sans_crf:
        X_train = phrases_vers_X(train)
        y_train = phrases_vers_y(train)
        crf = entrainer_crf(X_train, y_train, args.max_iter)
        X_test = phrases_vers_X(test)
        y_pred = crf.predict(X_test)
        rapport["crf"] = {
            "config": {"algorithm": "lbfgs", "c1": 0.1, "c2": 0.1,
                       "max_iterations": args.max_iter,
                       "features": "orthographiques + contexte ±2, sans "
                                   "listes externes"},
            "resultats": evaluer_spans(y_gold, y_pred),
        }

    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
