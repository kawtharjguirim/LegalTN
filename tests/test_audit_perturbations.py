"""Tests des perturbations INV de l'audit Gold."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.audit.perturbations import (faute_de_frappe, normalisation_alef, politesse, sans_accents,
                                     sans_ponctuation, variantes)


def test_sans_accents_et_ponctuation():
    assert sans_accents("Quelle est la durée légale ?") == "Quelle est la duree legale ?"
    assert sans_ponctuation("Un congé, payé : peut-il ?") == "Un congé payé peut-il"
    assert sans_ponctuation("هل يجوز ذلك؟") == "هل يجوز ذلك"


def test_faute_de_frappe_deterministe():
    assert faute_de_frappe("Quelle est la durée maximale ?") == "Quelle est la durée mxaimale ?"
    assert faute_de_frappe("Oui non") == "Oui non"


def test_politesse_et_alef():
    assert politesse("Quel est le délai ?", "fr") == "Bonjour, j'aimerais savoir : quel est le délai ?"
    assert politesse("ما هي المدة؟", "ar").startswith("السلام عليكم")
    assert normalisation_alef("أجل إعلام آخر") == "اجل اعلام اخر"


def test_variantes_selon_perimetre_et_langue():
    fr = variantes("Quelle est la durée maximale du travail ?", "fr", True)
    assert set(fr) == {"politesse", "faute_de_frappe", "sans_ponctuation", "sans_accents", "minuscules"}
    ar = variantes("هل للعامل الحق في عطلة بمناسبة ولادة طفله؟", "ar_trad", True)
    assert "normalisation_alef" not in ar or ar["normalisation_alef"] != "هل للعامل الحق في عطلة بمناسبة ولادة طفله؟"
    hors = variantes("Quelle est la capitale de la Tunisie ?", "fr", False)
    assert set(hors) == {"politesse", "faute_de_frappe"}
