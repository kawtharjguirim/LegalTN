"""Tests du pipeline NER CRF (features, spans, baseline, lots).

Aucune donnée gelée ni annotation humaine n'est utilisée ; les fixtures
sont synthétiques.
"""

import csv
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from src.ner_crf.features import mot_vers_features, phrases_vers_X, phrases_vers_y
from src.ner_crf.pipeline import (
    etiquettes_vers_spans, evaluer_spans, extraire_entites)
from src.ner_crf.reproduire_baseline_conll import (
    charger_conll, entites_majoritaires, entites_uniques, predire_baseline)
from src.evaluation.preparer_lots_independants import (
    GRAINE_RAPPEL, phrases_dev)


def test_features_bordures():
    s = [("Paris", "", "B-LOC"), ("est", "", "O"), ("grand", "", "O")]
    f0 = mot_vers_features(s, 0)
    f2 = mot_vers_features(s, 2)
    assert f0["BOS"] and f0["est_titre"]
    assert f2["EOS"] and "+1:mot.lower" not in f2
    assert mot_vers_features(s, 1)["-1:mot.lower"] == "paris"


def test_phrases_vers_xy():
    s = [[("A", "N", "O"), ("B", "V", "B-PER")]]
    assert phrases_vers_y(s) == [["O", "B-PER"]]
    assert len(phrases_vers_X(s)[0]) == 2


def test_spans_bio():
    tags = ["O", "B-PER", "I-PER", "O", "B-LOC", "I-ORG", "B-MISC"]
    spans = etiquettes_vers_spans(tags)
    assert (1, 3, "PER") in spans
    assert (4, 5, "LOC") in spans
    # I-ORG après B-LOC : nouveau span ORG orphelin (comportement conlleval)
    assert (5, 6, "ORG") in spans
    assert (6, 7, "MISC") in spans


def test_evaluer_spans_micro():
    gold = [["B-PER", "O", "B-LOC"], ["O"]]
    pred = [["B-PER", "O", "B-ORG"], ["B-LOC"]]
    res = evaluer_spans(gold, pred)["micro"]
    assert res["vp"] == 1 and res["n_gold"] == 2 and res["n_pred"] == 3
    assert res["rappel"] == 50.0 and res["precision"] == 33.33
    assert res["f1"] == 40.0


def test_extraire_entites():
    mots = ["Jean", "Durand", "travaille"]
    ents = extraire_entites(mots, ["B-PER", "I-PER", "O"])
    assert ents == [{"debut": 0, "fin": 2, "type": "PER",
                     "texte": "Jean Durand"}]


def test_charger_conll(tmp_path):
    f = tmp_path / "esp.train"
    f.write_text("-DOCSTART- O\n\nJuan B-PER\nPerez I-PER\n\ncorre O\n",
                 encoding="utf-8")
    s = charger_conll(f)
    assert s == [[("Juan", "", "B-PER"), ("Perez", "", "I-PER")],
                 [("corre", "", "O")]]


def test_baseline_dictionnaire_plus_long():
    train = [[("Real", "", "B-ORG"), ("Madrid", "", "I-ORG")],
             [("Madrid", "", "B-LOC")]]
    ents = entites_uniques(train)
    tags = predire_baseline(["en", "Real", "Madrid", "cf", "Madrid"], ents)
    assert tags[:3] == ["O", "B-ORG", "I-ORG"]
    assert tags[4] == "B-LOC"


def test_baseline_classe_ambigue_exclue():
    train = [[("Madrid", "", "B-LOC")], [("Madrid", "", "B-ORG")]]
    assert entites_uniques(train) == {}


def test_baseline_majoritaire():
    train = [[("Madrid", "", "B-LOC")], [("Madrid", "", "B-LOC")],
             [("Madrid", "", "B-ORG")]]
    assert entites_majoritaires(train) == {("Madrid",): "LOC"}


def test_phrases_dev_chargees():
    assert len(phrases_dev()) == 200


@pytest.mark.parametrize("nom", ["rappel_alignement_a_annoter_v1.csv",
                                 "ner_a_annoter_v1.csv"])
def test_lots_independants_generes(nom):
    """Les lots produits existent, ont des champs d'annotation vides et
    n'écrasent pas un fichier manuel préexistant (relance idempotente
    vérifiée séparément)."""
    lot = RACINE / "data/dev" / nom
    if not lot.exists():
        pytest.skip("lot pas encore généré")
    with open(lot, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f))
    assert lignes
    champ_annotation = "verdict_image" if "rappel" in nom else "entites"
    assert all(l[champ_annotation] == "" for l in lignes)


def test_lot_obligations_test_disjoint_dev():
    lot = RACINE / "data/test_locked/obligations_candidats_test_v1.csv"
    if not lot.exists():
        pytest.skip("lot test pas encore généré")
    with open(lot, encoding="utf-8-sig", newline="") as f:
        test = list(csv.DictReader(f))
    norm = lambda t: " ".join(t.split()).lower()
    dev_norm = {norm(p) for p in phrases_dev()}
    assert all(norm(l["phrase"]) not in dev_norm for l in test)
    assert all(l["modal"] == "" and l["qui"] == "" for l in test)


def test_graine_rappel_documentee():
    assert GRAINE_RAPPEL == 20261030
