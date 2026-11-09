"""Tests de src/evaluation/calculer_kappa.py (fichiers synthétiques temporaires)."""
import csv
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
import calculer_kappa as ck  # noqa: E402


def ecrire(chemin, lignes, colonnes=("obligation_id", "modal")):
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        w.writeheader()
        w.writerows(lignes)
    return chemin


def test_refuse_si_fichiers_vides(tmp_path):
    a = ecrire(tmp_path / "a.csv", [{"obligation_id": "O1", "modal": ""}])
    b = ecrire(tmp_path / "b.csv", [{"obligation_id": "O1", "modal": ""}])
    with pytest.raises(ck.RefusDeCalcul):
        ck.calculer(a, b, "obligation_id", "modal")
    assert ck.main(["--a", str(a), "--b", str(b), "--id", "obligation_id", "--champ", "modal"]) == 2


def test_refuse_si_fichier_absent(tmp_path):
    a = ecrire(tmp_path / "a.csv", [{"obligation_id": "O1", "modal": "obligation"}])
    assert ck.main(["--a", str(a), "--b", str(tmp_path / "absent.csv"),
                    "--id", "obligation_id", "--champ", "modal"]) == 2


def test_kappa_cas_connu(tmp_path):
    # Exemple classique : 50 items, accord observé 0,70, attendu 0,50 -> kappa 0,40.
    va = ["oui"] * 25 + ["non"] * 25
    vb = ["oui"] * 20 + ["non"] * 5 + ["oui"] * 10 + ["non"] * 15
    a = ecrire(tmp_path / "a.csv", [{"obligation_id": f"O{i}", "modal": v} for i, v in enumerate(va)])
    b = ecrire(tmp_path / "b.csv", [{"obligation_id": f"O{i}", "modal": v} for i, v in enumerate(vb)])
    r = ck.calculer(a, b, "obligation_id", "modal")
    assert r["n"] == 50 and r["accord_observe"] == 0.7 and r["accord_attendu"] == 0.5 and r["kappa"] == 0.4


def test_lignes_vides_ignorees_pas_comptees_comme_desaccord(tmp_path):
    a = ecrire(tmp_path / "a.csv", [{"obligation_id": "O1", "modal": "obligation"},
                                    {"obligation_id": "O2", "modal": "permission"}])
    b = ecrire(tmp_path / "b.csv", [{"obligation_id": "O1", "modal": "obligation"},
                                    {"obligation_id": "O2", "modal": ""}])
    assert ck.calculer(a, b, "obligation_id", "modal")["n"] == 1


def test_accord_spans_ner(tmp_path):
    cols = ("item_id", "entites")
    a = ecrire(tmp_path / "a.csv", [{"item_id": "N1", "entites": "0|12|ROLE;20|30|DELAI"}], cols)
    b = ecrire(tmp_path / "b.csv", [{"item_id": "N1", "entites": "0|12|ROLE;40|45|MONTANT"}], cols)
    r = ck.calculer(a, b, "item_id", "entites", mode="spans")
    assert r["communes"] == 1 and r["accord_F1"] == 0.5
