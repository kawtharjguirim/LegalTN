"""Tests du RAG sans modèle : fusion RRF, seuil leave-one-out, citations, prompts."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rag.evaluer import questions, seuil_loo
from src.rag.generer import ABSTENTION, citations, construire_prompt
from src.rag.recherche import Resultat, dedoublonner, rrf


def test_rrf_favorise_accord_des_classements():
    s = rrf([["a", "b", "c"], ["b", "a", "d"]], k=60)
    assert s["a"] == s["b"] > s["c"] == s["d"]


def test_dedoublonner_garde_meilleure_ligne():
    articles = [{"article": "6"}, {"article": "6"}, {"article": "7"}]
    assert dedoublonner([1, 0, 2], [0.5, 0.9, 0.1], articles) == [("6", 0.9, 1), ("7", 0.1, 2)]


def test_seuil_loo_separe_les_classes():
    scores = np.array([0.9, 0.85, 0.8, 0.3, 0.2, 0.25])
    dans = np.array([True, True, True, False, False, False])
    abst, seuil = seuil_loo(scores, dans)
    assert abst.tolist() == [False, False, False, True, True, True]
    assert 0.3 < seuil <= 0.8


def test_citations_normalisees():
    assert citations("Voir [Article 14 bis] et [article 23].") == ["14 bis", "23"]


def test_prompt_few_shot_contient_exemples_et_contexte():
    r = [Resultat("23", 1.0, "fr", "280", "Article 23.- La rupture abusive ...")]
    m = construire_prompt("Question ?", r, "fr", "few_shot")
    assert m[0]["role"] == "system" and len(m) == 6
    assert "[Article 23]" in m[-1]["content"]
    assert ABSTENTION["fr"] in m[0]["content"]


def test_prompt_zero_shot_arabe():
    m = construire_prompt("سؤال؟", [], "ar", "zero_shot")
    assert len(m) == 2 and ABSTENTION["ar"] in m[0]["content"]


def test_questions_dev_chargees():
    q = questions()
    assert {l["langue"] for l in q} == {"fr", "tun", "ar", "ar_trad"}
    assert all(l["reference"] for l in q if l["dans"])
    assert not any(l["reference"].endswith(".0") for l in q)
