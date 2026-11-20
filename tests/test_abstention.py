"""Tests de la règle d'abstention de la démo (palier Gold)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rag.service import SEUILS, SEUILS_BRUT, abstenir


def test_francais_signal_normalise_seulement():
    s = SEUILS["fr"]
    assert abstenir({"cosnorm_max": s - 0.01, "cos_max": 0.99}, "fr")
    # Un cosinus brut faible (question sans accents) ne suffit pas à s'abstenir en français.
    assert not abstenir({"cosnorm_max": s + 0.01, "cos_max": 0.10}, "fr")


def test_arabe_brut_ou_normalise():
    n, b = SEUILS["ar"], SEUILS_BRUT["ar"]
    assert not abstenir({"cosnorm_max": n + 0.01, "cos_max": b + 0.01}, "ar")
    assert abstenir({"cosnorm_max": n + 0.01, "cos_max": b - 0.01}, "ar")   # cas « رخصة اسلياقة »
    assert abstenir({"cosnorm_max": n - 0.01, "cos_max": b + 0.01}, "ar")
