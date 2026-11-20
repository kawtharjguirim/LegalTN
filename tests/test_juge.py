import math

from src.juge.juge import RE_VERDICT, binaire, kappa


def test_kappa_accord_parfait():
    assert kappa(["fidele", "partiel", "infidele"], ["fidele", "partiel", "infidele"]) == 1.0


def test_kappa_valeur_connue():
    # po = 0.75 ; pe = 0.5*0.5 + 0.5*0.5 = 0.5 -> kappa = 0.5
    a = ["fidele", "fidele", "infidele", "infidele"]
    b = ["fidele", "fidele", "infidele", "fidele"]
    assert math.isclose(kappa(a, b), 0.5)


def test_kappa_hasard_et_vide():
    a = ["fidele", "infidele"] * 2
    b = ["fidele", "fidele", "infidele", "infidele"]
    assert math.isclose(kappa(a, b), 0.0)
    assert math.isnan(kappa([], []))


def test_binaire_et_lecture_verdict():
    assert binaire("partiel") == "non_fidele" and binaire("fidele") == "fidele"
    assert RE_VERDICT.search("VERDICT: INFIDÈLE | contredit").group(1).upper() == "INFIDÈLE"
    assert RE_VERDICT.search("verdict : partiel | incomplet").group(1).lower() == "partiel"
    assert RE_VERDICT.search("INFIDELE | contredit l'article").group(1) == "INFIDELE"
    assert RE_VERDICT.search("FIDELE | la réponse n'est pas infidèle").group(1) == "FIDELE"
    assert RE_VERDICT.search("VERDILE | mot déformé") is None
