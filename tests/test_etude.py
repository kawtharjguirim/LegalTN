import csv
import math
from pathlib import Path

import pytest

from src.etude import analyser as an

RACINE = Path(__file__).resolve().parents[1]
REF = RACINE / "etude_utilite/taches_v1.csv"


def test_taches_de_reference_equilibrees():
    lignes = an.lire(REF)
    assert len(lignes) == 12
    for ens in ("A", "B"):
        g = [l for l in lignes if l["ensemble"] == ens]
        assert len(g) == 6 and sum(l["dans_perimetre"] == "non" for l in g) == 1
    for l in lignes:
        assert (l["article_reference"] == "") == (l["dans_perimetre"] == "non")


def test_page_ne_contient_pas_le_corrige():
    page = (RACINE / "outils/etude_utilite.html").read_text(encoding="utf-8")
    for l in an.lire(REF):
        assert l["reponse_attendue"][:40] not in page          # le corrigé reste côté facilitateur
        assert l["enonce"][:60] in page                         # mais les énoncés sont identiques


def test_permutation_exacte_et_bootstrap():
    # 6 différences toutes positives : seule 1 inversion de signe sur 64 (et son opposée) est aussi extrême
    assert math.isclose(an.permutation_p([1.0] * 6), 2 / 64)
    lo, hi = an.bootstrap_ic([1.0, 1.0, 1.0, 1.0])
    assert lo == hi == 1.0


def _ecrire(dossier: Path, n: int = 6):
    champs = ["participant", "groupe", "bloc", "condition", "ensemble", "tache_id", "reponse", "article_cite",
              "non_trouve", "confiance", "duree_s", "note_reponse", "note_article"]
    ids = {"A": ["E01", "E02", "E03", "E04", "E05", "E06"], "B": ["E07", "E08", "E09", "E10", "E11", "E12"]}
    for i in range(n):
        p = f"P{i + 1:02d}"
        lignes = []
        for cond, ens in (("LegalTN", "A"), ("Code", "B")):
            for t in ids[ens]:
                hors = t in ("E06", "E12")
                ok = 1 if cond == "LegalTN" or (i % 2 == 0) else 0       # Code : moitié des participants se trompent
                lignes.append({"participant": p, "groupe": "G1", "bloc": 1, "condition": cond, "ensemble": ens, "tache_id": t,
                               "reponse": "x", "article_cite": "1", "non_trouve": int(hors), "confiance": 4,
                               "duree_s": 60 if cond == "LegalTN" else 120, "note_reponse": ok, "note_article": ok})
        with open(dossier / f"{p}_taches.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=champs)
            w.writeheader()
            w.writerows(lignes)
        with open(dossier / f"{p}_questionnaires.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["participant", "condition", "sus_score", "preference"])
            w.writeheader()
            w.writerow({"participant": p, "condition": "LegalTN", "sus_score": 80, "preference": "LegalTN"})
            w.writerow({"participant": p, "condition": "Code", "sus_score": 60, "preference": "LegalTN"})


def test_analyse_sur_donnees_simulees(tmp_path):
    _ecrire(tmp_path)
    res = an.analyser(tmp_path, REF)
    assert res["n_participants"] == 6
    ex = res["comparaisons"]["exactitude"]
    assert ex["legaltn"] == 1.0 and ex["code"] == 0.5 and ex["difference"] == 0.5
    assert res["comparaisons"]["temps_median_s"]["difference"] == -60.0
    assert res["sus"]["difference"] == 20.0
    assert res["preferences"] == {"LegalTN": 12}
    assert "| Exactitude" in an.markdown(res)


def test_refuse_sans_notes(tmp_path):
    _ecrire(tmp_path, 2)
    f = tmp_path / "P01_taches.csv"
    lignes = an.lire(f)
    lignes[0]["note_reponse"] = ""
    with open(f, "w", encoding="utf-8-sig", newline="") as sortie:
        w = csv.DictWriter(sortie, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    with pytest.raises(SystemExit, match="non notées"):
        an.analyser(tmp_path, REF)
