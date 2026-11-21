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


def test_accord_humain_relit_les_juges(tmp_path, monkeypatch):
    import csv
    import json

    from src.juge import juge

    ech = tmp_path / "ech.csv"
    champs = ["id", "langue", "verdict_humain", "verdict_claude", "commentaire", "commentaire_humain"]
    with open(ech, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerow({"id": "J01", "langue": "fr", "verdict_humain": "fidele", "verdict_claude": "fidele"})
        w.writerow({"id": "J02", "langue": "ar", "verdict_humain": "infidele", "verdict_claude": "partiel"})
        w.writerow({"id": "J03", "langue": "fr", "verdict_humain": "", "verdict_claude": "fidele"})  # non jugée : ignorée
    with open(tmp_path / "juge_m.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "verdict_juge"])
        w.writeheader()
        w.writerows([{"id": "J01", "verdict_juge": "fidele"}, {"id": "J02", "verdict_juge": "infidele"},
                     {"id": "J03", "verdict_juge": "infidele"}])
    monkeypatch.setattr(juge, "ECHANTILLON", ech)
    juge.accord_humain(tmp_path)
    res = json.loads((tmp_path / "accord_humain.json").read_text(encoding="utf-8"))
    assert res["n_jugees_humain"] == 2
    assert res["humain_vs_m"]["accord_brut_3_classes"] == 1.0
    assert res["humain_vs_claude"]["accord_brut_3_classes"] == 0.5
