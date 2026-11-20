"""Tests de la catégorisation des erreurs NER sur gold."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ner_juridique.evaluer_gold import categoriser

P = "L'employeur informe l'inspection du travail dans un délai de quinze jours."


def cats(gold, pred):
    return sorted(e["categorie"] for e in categoriser(gold, pred, P))


def test_correct_aucune_erreur():
    assert cats([(0, 11, "ROLE")], [(0, 11, "ROLE")]) == []


def test_f1_souple_compte_les_chevauchements_de_meme_type():
    from src.ner_juridique.donnees import f1_chevauchement, f1_spans
    gold = [[(44, 73, "DELAI"), (0, 11, "ROLE")]]
    pred = [[(60, 73, "DELAI"), (0, 11, "INSTITUTION")]]
    assert f1_spans(gold, pred)["micro"]["f1"] == 0.0
    assert f1_chevauchement(gold, pred)["f1"] == 0.5


def test_frontiere_type_oubli_faux_positif():
    gold = [(0, 11, "ROLE"), (20, 43, "INSTITUTION"), (44, 73, "DELAI")]
    pred = [(2, 11, "ROLE"), (20, 43, "ROLE"), (12, 19, "MONTANT")]
    assert cats(gold, pred) == ["faux_positif", "frontiere", "oubli", "type"]
