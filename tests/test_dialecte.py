import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from traduction import dialecte  # noqa: E402


def test_candidats():
    assert dialecte.est_candidat("قداش من ساعة نجم نخدم في الجمعة؟")
    assert dialecte.est_candidat("chhal men se3a nekhdem fel jem3a?")
    assert dialecte.est_candidat("mrati weldet 3andi 7a9 fi ra7a?")
    assert not dialecte.est_candidat("Quelle est la durée maximale du travail effectif par semaine ?")
    assert not dialecte.est_candidat("Un salarié a-t-il droit à un congé à l'occasion de la naissance ?")


def test_francais_jamais_envoye():
    def interdit(q, cle):
        raise AssertionError("ne doit pas appeler l'API")
    r = dialecte.traduire("Quelle est la période d'essai ?", appeler=interdit)
    assert r["source"] == "aucune" and r["question"] == "Quelle est la période d'essai ?"


def test_repli_si_erreur(monkeypatch, tmp_path):
    monkeypatch.setattr(dialecte, "CACHE", tmp_path / "c.json")
    monkeypatch.setattr(dialecte, "_cle_api", lambda: "x")
    def panne(q, cle):
        raise OSError("hors ligne")
    r = dialecte.traduire("chhal men se3a nekhdem?", appeler=panne)
    assert r["source"] == "repli" and r["question"] == "chhal men se3a nekhdem?"


def test_sortie_non_arabe_refusee(monkeypatch, tmp_path):
    monkeypatch.setattr(dialecte, "CACHE", tmp_path / "c.json")
    monkeypatch.setattr(dialecte, "_cle_api", lambda: "x")
    r = dialecte.traduire("chhal men se3a nekhdem?", appeler=lambda q, c: "Quelle est la capitale ?")
    assert r["source"] == "repli" and r["erreur"] == "sortie_non_arabe"


def test_traduction_mise_en_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(dialecte, "CACHE", tmp_path / "c.json")
    monkeypatch.setattr(dialecte, "_cle_api", lambda: "x")
    r = dialecte.traduire("قداش نخدم؟", appeler=lambda q, c: "كم ساعة أعمل؟")
    assert r["traduite"] and r["question"] == "كم ساعة أعمل؟"
    r2 = dialecte.traduire("قداش نخدم؟", appeler=lambda q, c: (_ for _ in ()).throw(AssertionError()))
    assert r2["source"] == "cache"
