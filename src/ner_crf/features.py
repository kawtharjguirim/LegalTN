"""Traits orthographiques et contextuels pour le CRF de NER.

Une phrase est une liste de tuples ``(mot, pos, etiquette)`` ; ``pos`` peut
être vide (corpus espagnol de CoNLL-2002, corpus LegalTN non étiqueté).
"""

from __future__ import annotations


def mot_vers_features(phrase: list, i: int) -> dict:
    mot, pos = phrase[i][0], phrase[i][1]
    f = {
        "bias": 1.0,
        "mot.lower": mot.lower(),
        "mot[-3:]": mot[-3:],
        "mot[-2:]": mot[-2:],
        "est_majuscule": mot.isupper(),
        "est_titre": mot.istitle(),
        "est_chiffre": mot.isdigit(),
        "pos": pos,
    }
    if i == 0:
        f["BOS"] = True
    else:
        m1, p1 = phrase[i - 1][0], phrase[i - 1][1]
        f.update({
            "-1:mot.lower": m1.lower(), "-1:est_majuscule": m1.isupper(),
            "-1:est_titre": m1.istitle(), "-1:pos": p1,
        })
        if i > 1:
            f["-2:mot.lower"] = phrase[i - 2][0].lower()
            f["-2:pos"] = phrase[i - 2][1]
    if i == len(phrase) - 1:
        f["EOS"] = True
    else:
        m2, p2 = phrase[i + 1][0], phrase[i + 1][1]
        f.update({
            "+1:mot.lower": m2.lower(), "+1:est_majuscule": m2.isupper(),
            "+1:est_titre": m2.istitle(), "+1:pos": p2,
        })
        if i < len(phrase) - 2:
            f["+2:mot.lower"] = phrase[i + 2][0].lower()
            f["+2:pos"] = phrase[i + 2][1]
    return f


def phrases_vers_X(phrases: list) -> list:
    return [[mot_vers_features(s, i) for i in range(len(s))] for s in phrases]


def phrases_vers_y(phrases: list) -> list:
    return [[t[2] for t in s] for s in phrases]
