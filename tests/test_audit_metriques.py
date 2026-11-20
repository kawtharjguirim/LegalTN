"""Tests des métriques de l'audit Gold sur des lignes synthétiques (sans LLM)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.audit.audit import abstention_par_langue, construire_jeu, hallucinations, invariance


def ligne(source, type_, rep=0, top1="79", abst=False, cit="79", dans=True, langue="fr",
          invente=False, llm=True):
    return {"source": source, "type": type_, "repetition": rep, "top1": top1, "abstention": abst,
            "abstention_recherche": abst and not llm, "abstention_llm": abst if llm else None,
            "citations": "" if abst else cit, "dans": dans, "langue": langue, "reference": "79",
            "llm_appele": llm, "invente": invente, "hors_contexte_brut": invente, "sans_citation": False}


def test_invariance_et_bruit_de_reference():
    lignes = [ligne("D31", "original"), ligne("D31", "original", rep=1),
              ligne("D31", "original", rep=2, cit="88"),
              ligne("D31", "sans_accents"), ligne("D31", "faute_de_frappe", top1="88", cit="88")]
    inv = invariance(lignes)
    assert inv["bruit_reference (original répété)"] == {"n": 2, "recherche": 1.0, "decision": 1.0, "citations": 0.5}
    assert inv["sans_accents"]["citations"] == 1.0
    assert inv["faute_de_frappe"]["recherche"] == 0.0


def test_hallucinations_et_abstention():
    lignes = [ligne("D31", "original"), ligne("D32", "original", invente=True, cit="999"),
              ligne("H1", "original", dans=False, abst=True, llm=False, top1="")]
    h = hallucinations(lignes)
    assert h["reponses_llm"] == 2 and h["article_invente_brut"] == 0.5
    assert h["hors_perimetre_avec_reponse"] == 0.0
    a = abstention_par_langue(lignes)["fr"]
    assert a["reference_citee"] == 0.5 and a["abstention_correcte_hors"] == 1.0


def test_jeu_complet():
    jeu = construire_jeu()
    types = {l["type"] for l in jeu}
    assert {"original", "paraphrase", "politesse", "faute_de_frappe", "sans_accents"} <= types
    assert all(l["type"] == "original" for l in jeu if l["langue"] == "tun")
    assert sum(l["type"] == "paraphrase" for l in jeu) == 42
