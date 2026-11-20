"""Tests des conversions spans <-> BIO et de la métrique F1 par span (sans modèle)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ner_juridique.donnees import f1_spans, separer_validation
from src.ner_juridique.entrainer import (E2I, ETIQUETTES, etiquettes_tokens, mots,
                                         spans_depuis_tokens)

PHRASE = "L'employeur paie 300 dinars."
ENTITES = [(0, 11, "ROLE"), (17, 27, "MONTANT")]


def test_etiquettes_tokens_bio():
    offsets = [(0, 0), (0, 2), (2, 11), (12, 16), (17, 20), (21, 27), (27, 28), (0, 0)]
    labels = [ETIQUETTES[i] if i >= 0 else None for i in etiquettes_tokens(offsets, ENTITES)]
    assert labels == [None, "B-ROLE", "I-ROLE", "O", "B-MONTANT", "I-MONTANT", "O", None]


def test_aller_retour_spans():
    offsets = [(0, 2), (2, 11), (12, 16), (17, 20), (21, 27), (27, 28)]
    labels = [ETIQUETTES[i] for i in etiquettes_tokens(offsets, ENTITES)]
    assert spans_depuis_tokens(offsets, labels, PHRASE) == ENTITES


def test_i_orphelin_ouvre_une_entite():
    assert spans_depuis_tokens([(0, 3), (4, 8)], ["I-ROLE", "I-ROLE"], "abc defg") == [(0, 8, "ROLE")]


def test_offsets_chevauchants_fusionnes():
    # « vingt heures » : XLM-R produit « ▁ » (5, 6) puis « vingt » (5, 10), tous deux en B.
    p = "pour vingt heures"
    offsets = [(0, 4), (5, 6), (5, 10), (11, 17)]
    labels = ["O", "B-MONTANT", "B-MONTANT", "I-MONTANT"]
    assert spans_depuis_tokens(offsets, labels, p) == [(5, 17, "MONTANT")]


def test_mots_offsets():
    assert [(w, d, f) for w, d, f in mots("Il paie.")] == [("Il", 0, 2), ("paie", 3, 7), (".", 7, 8)]


def test_f1_exact():
    m = f1_spans([ENTITES], [[(0, 11, "ROLE"), (17, 20, "MONTANT")]])
    assert m["micro"]["precision"] == 0.5 and m["micro"]["rappel"] == 0.5
    assert m["par_type"]["ROLE"]["f1"] == 1.0 and m["par_type"]["MONTANT"]["f1"] == 0.0
    assert m["macro_f1"] == 0.5


def test_validation_par_article():
    lignes = [{"article": f"A{i % 10}", "phrase": str(i)} for i in range(50)]
    train, val = separer_validation(lignes, part=0.2, graine=1)
    assert {l["article"] for l in train}.isdisjoint({l["article"] for l in val})
    assert len(train) + len(val) == 50


def test_etiquettes_completes():
    assert len(ETIQUETTES) == 9 and E2I["O"] == 0
