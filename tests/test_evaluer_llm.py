"""Tests des fonctions d'analyse des réponses du LLM (sans appel au modèle)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rag.evaluer_llm import mentions, part_arabe, taux


def test_mentions_texte_libre_fr_et_ar():
    assert mentions("comme le stipule l'article 79 du Code") == ["79"]
    assert mentions("voir l'Article 14 bis et l'article 23") == ["14 bis", "23"]
    assert mentions("حسب الفصل 6 مكرر") == ["6 bis"]


def test_part_arabe():
    assert part_arabe("مدة الإعلام شهر") == 1.0
    assert part_arabe("Le préavis est d'un mois") == 0.0
    assert part_arabe("") == 0.0


def test_taux():
    assert taux(1, 4) == 0.25
    assert taux(0, 0) is None
