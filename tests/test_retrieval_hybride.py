"""Tests de la fusion RRF et des garde-fous de l'évaluation (sans modèle neuronal)."""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src" / "evaluation"))

from retrieval.hybride import K_RRF, dedupliquer, fusion_rrf  # noqa: E402


def test_dedupliquer_garde_premiere_occurrence():
    assert dedupliquer(["6", "5", "6", "7", "5"]) == ["6", "5", "7"]


def test_rrf_scores_exacts():
    res = dict(fusion_rrf([["a", "b"], ["b", "c"]]))
    assert res["b"] == pytest.approx(1 / (K_RRF + 2) + 1 / (K_RRF + 1))
    assert res["a"] == pytest.approx(1 / (K_RRF + 1))
    assert res["c"] == pytest.approx(1 / (K_RRF + 2))


def test_rrf_article_present_partout_passe_devant():
    ordre = [lab for lab, _ in fusion_rrf([["a", "b", "c"], ["c", "b", "a"], ["b"]])]
    assert ordre[0] == "b"


def test_rrf_doublons_comptent_une_fois():
    assert dict(fusion_rrf([["a", "a", "b"]]))["b"] == pytest.approx(1 / (K_RRF + 2))


def test_rrf_egalite_deterministe():
    assert [lab for lab, _ in fusion_rrf([["a"], ["b"]])] == ["a", "b"]


def test_rrf_classement_vide():
    assert fusion_rrf([[], []]) == []


def test_evaluation_refuse_le_test_gele():
    import evaluer_retrieval
    with pytest.raises(ValueError):
        evaluer_retrieval.verifier_jeu(RACINE / "data" / "test_locked" / "questions_reference_v2.csv")
