"""Entraînement, prédiction et évaluation par spans du CRF NER."""

from __future__ import annotations


def entrainer_crf(X_train, y_train, max_iterations: int = 100):
    import sklearn_crfsuite

    crf = sklearn_crfsuite.CRF(
        algorithm="lbfgs", c1=0.1, c2=0.1,
        max_iterations=max_iterations, all_possible_transitions=True,
    )
    crf.fit(X_train, y_train)
    return crf


def etiquettes_vers_spans(etiquettes: list) -> set:
    """BIO -> ensemble {(debut, fin_exclu, type)} ; les I- orphelins ouvrent
    un span de leur propre type (comportement conlleval)."""
    spans, debut, type_ = set(), None, None
    for i, tag in enumerate(etiquettes + ["O"]):
        if tag.startswith("B-"):
            if type_ is not None:
                spans.add((debut, i, type_))
            debut, type_ = i, tag[2:]
        elif tag.startswith("I-"):
            if type_ is None:
                debut, type_ = i, tag[2:]
            elif tag[2:] != type_:
                spans.add((debut, i, type_))
                debut, type_ = i, tag[2:]
        else:
            if type_ is not None:
                spans.add((debut, i, type_))
            debut, type_ = None, None
    return spans


def evaluer_spans(y_gold: list, y_pred: list) -> dict:
    """Précision/rappel/F1 micro et par type, en correspondance exacte."""
    par_type: dict[str, dict] = {}
    totaux = {"vp": 0, "pred": 0, "gold": 0}
    for type_ in ("PER", "ORG", "LOC", "MISC"):
        par_type[type_] = {"vp": 0, "pred": 0, "gold": 0}
    for eg, ep in zip(y_gold, y_pred):
        sg, sp = etiquettes_vers_spans(list(eg)), etiquettes_vers_spans(list(ep))
        totaux["gold"] += len(sg)
        totaux["pred"] += len(sp)
        totaux["vp"] += len(sg & sp)
        for s in sg:
            par_type[s[2]]["gold"] += 1
        for s in sp:
            par_type[s[2]]["pred"] += 1
        for s in sg & sp:
            par_type[s[2]]["vp"] += 1

    def prf(d):
        p = d["vp"] / d["pred"] if d["pred"] else 0.0
        r = d["vp"] / d["gold"] if d["gold"] else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p * 100, 2), "rappel": round(r * 100, 2),
                "f1": round(f1 * 100, 2), "vp": d["vp"],
                "n_pred": d["pred"], "n_gold": d["gold"]}

    return {"micro": prf(totaux),
            "par_type": {t: prf(d) for t, d in par_type.items()}}


def extraire_entites(mots: list, etiquettes: list) -> list:
    spans = sorted(etiquettes_vers_spans(list(etiquettes)))
    return [{"debut": d, "fin": f, "type": t,
             "texte": " ".join(mots[d:f])} for d, f, t in spans]
