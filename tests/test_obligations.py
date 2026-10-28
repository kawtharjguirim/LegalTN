"""Tests du module d'extraction d'obligations et de son évaluateur.

Les phrases ci-dessous sont des fixtures écrites pour les tests ; elles ne
constituent pas des annotations du corpus.
"""

import csv
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from src.obligation_extraction.extraire_obligations import (
    analyser_phrase, est_definition, extraire_depuis_csv,
    extraire_quand, trouver_modal)
from src.obligation_extraction.evaluer_obligations import (
    annotations_disponibles, evaluer)


def test_modal_obligation():
    modal, _ = trouver_modal(
        "L'employeur doit remettre un carnet à chaque salarié.")
    assert modal == "obligation"


def test_modal_interdiction_avant_permission():
    modal, _ = trouver_modal(
        "Le salarié ne peut être requis pour ce travail.")
    assert modal == "interdiction"


def test_modal_permission():
    modal, _ = trouver_modal(
        "Le travailleur peut demander sa radiation.")
    assert modal == "permission"


def test_sans_marqueur():
    assert trouver_modal("Le ciel est bleu.") == (None, None)


def test_definition_non_obligation():
    assert est_definition("On entend par salarié toute personne.")
    a = analyser_phrase("On entend par salarié toute personne.")
    assert not a["est_obligation_predite"]


def test_qui_role_avant_modal():
    a = analyser_phrase(
        "L'employeur doit verser le salaire dans les huit jours.")
    assert a["est_obligation_predite"]
    assert "employeur" in a["qui_predit"].lower()


def test_quand_condition():
    q = extraire_quand(
        "Le préavis doit être donné au moins un mois avant le départ.")
    assert q
    a = analyser_phrase(
        "En cas de faute grave, l'employeur peut suspendre le contrat.")
    assert a["quand_predit"].lower().startswith("en cas de")


def test_extraction_csv(tmp_path):
    src = tmp_path / "candidats.csv"
    with open(src, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["obligation_id", "article_fr",
                                        "page_fr", "phrase"])
        w.writeheader()
        w.writerow({"obligation_id": "X1", "article_fr": "FR-1",
                    "page_fr": "1",
                    "phrase": "L'employeur doit respecter les règles."})
    sortie = tmp_path / "pred.csv"
    assert extraire_depuis_csv(src, sortie) == 1
    with open(sortie, encoding="utf-8") as f:
        lig = list(csv.DictReader(f))[0]
    assert lig["modal_predit"] == "obligation"
    assert lig["est_obligation_predite"] == "True"


def _lig(i, modal="", qui="", quand="", commentaire=""):
    return {"obligation_id": i, "article_fr": "FR-1", "page_fr": "1",
            "phrase": "p", "modal": modal, "qui": qui, "quand": quand,
            "commentaire": commentaire}


def _pred(i, obl=True, modal="obligation"):
    return {"obligation_id": i, "est_obligation_predite": str(obl),
            "modal_predit": modal, "qui_predit": "", "quand_predit": ""}


def test_annotations_disponibles_ignore_vides():
    gold = [_lig("a", "obligation"), _lig("b"),
            _lig("c", commentaire="non_obligation")]
    assert [g["obligation_id"] for g in annotations_disponibles(gold)] == [
        "a", "c"]


def test_evaluer_refuse_sans_ids_communs():
    with pytest.raises(ValueError):
        evaluer([_lig("x", "obligation")], [_pred("y")])


def test_evaluer_metriques_modal():
    gold = [_lig("a", "obligation"), _lig("b", "interdiction"),
            _lig("c", "permission"), _lig("d", commentaire="non_obligation")]
    preds = [_pred("a", True, "obligation"), _pred("b", True, "obligation"),
             _pred("c", False), _pred("d", True, "permission")]
    bilan = evaluer(gold, preds)
    det = bilan["resultats"]["detection_obligation"]
    assert det["vp"] == 2 and det["fp"] == 1 and det["fn"] == 1
    inter = bilan["resultats"]["modal_par_classe"]["interdiction"]
    assert inter["vp"] == 0 and inter["fn"] == 1
    assert bilan["resultats"]["n_erreurs"] == 3


def test_evaluateur_refuse_modele_vide(tmp_path):
    from src.obligation_extraction.evaluer_obligations import main
    gold = tmp_path / "g.csv"
    gold.write_text("obligation_id,article_fr,page_fr,phrase,qui,modal,"
                    "quoi,quand,commentaire\nA,FR-1,1,p,,,,,\n",
                    encoding="utf-8")
    assert main(["--gold", str(gold), "--predictions", str(gold),
                 "--sortie", str(tmp_path / "s.json")]) == 2
