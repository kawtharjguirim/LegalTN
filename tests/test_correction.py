"""Tests du correcteur orthographique SymSpell (src/correction/correcteur_symspell.py)."""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
sys.path.insert(0, str(RACINE / "src" / "demo"))

from src.correction.correcteur_symspell import correcteur, normaliser_ar, reduire_ar  # noqa: E402
import repondre  # noqa: E402


@pytest.fixture(scope="module")
def c():
    return correcteur()


def apres(resultat):
    return [x["apres"] for x in resultat["corrections"]]


def test_preavi_devient_preavis(c):
    r = c.corriger("Quel est le préavi de licenciement ?")
    assert r["question_corrigee"] == "Quel est le préavis de licenciement ?"
    assert apres(r) == ["préavis"]


def test_contart_devient_contrat(c):
    r = c.corriger("Rupture du contart de travail")
    assert r["question_corrigee"] == "Rupture du contrat de travail"


def test_question_correcte_inchangee(c):
    q = "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"
    r = c.corriger(q)
    assert r["question_corrigee"] == q
    assert r["corrections"] == []


def test_nombre_intact(c):
    r = c.corriger("Que dit l'article 14 sur les 30 jours de congé ?")
    assert "14" in r["question_corrigee"] and "30" in r["question_corrigee"]
    assert r["corrections"] == []


def test_cdi_expanse(c):
    r = c.corriger("Quel est le délai de préavis pour rompre un CDI ?")
    assert r["question_corrigee"] == "Quel est le délai de préavis pour rompre un contrat à durée indéterminée ?"
    assert r["corrections"] == [{"type": "sigle", "avant": "CDI", "apres": "contrat à durée indéterminée"}]


def test_sigle_sans_doublon(c):
    # « contrat CDI » ne doit pas donner « contrat contrat à durée indéterminée ».
    r = c.corriger("Quel est le préavis pour un contrat CDI ?")
    assert r["question_corrigee"] == "Quel est le préavis pour un contrat à durée indéterminée ?"
    r = c.corriger("quel est le préavi pour un contart CDI ?")
    assert r["question_corrigee"] == "quel est le préavis pour un contrat à durée indéterminée ?"


def test_mot_correct_absent_du_code_non_corrige(c):
    # « capitale » n'est pas dans le Code mais c'est un mot français : on n'y touche pas.
    assert c.corriger("Quelle est la capitale de la Tunisie ?")["corrections"] == []


def test_nom_propre_intact(c):
    assert c.corriger("Les règles de stationnement à Sousse")["corrections"] == []


def test_arabizi_non_corrige(c):
    q = "Ken el congé mta3i 5 ayem, lezem ykoun mtawel wela yemken yet9assem ?"
    assert c.corriger(q)["question_corrigee"] == q


def test_mots_courts_jamais_corriges(c):
    assert c.corriger_mot("xz", "fr") is None


def test_normalisation_arabe():
    assert normaliser_ar("أإآ") == "ااا"
    assert normaliser_ar("مدة") == "مده"
    assert normaliser_ar("عَقْدٌ") == "عقد"          # diacritiques retirés
    assert normaliser_ar("الشـــغل") == "الشغل"      # tatweel retiré
    assert reduire_ar("والعمال") == ("وال", "عمال", "")


def test_arabe_faute_corrigee_et_mot_correct_intact(c):
    assert c.corriger("عقد الشغلل", "ar")["question_corrigee"] == "عقد الشغل"
    assert c.corriger("عقد الشغل", "ar")["corrections"] == []


def test_chaine_demo_repond_sur_cdi_grace_au_lexique():
    # Le BM25 seul s'abstient (cf. xfail de test_evaluation.py) ; la chaîne corrigée répond.
    corpus = repondre.charger()
    r = repondre.repondre_question(corpus, "Quel est le délai de préavis pour rompre un CDI ?")
    assert r["abstention"] is False
    assert r["question_originale"] != r["question_corrigee"]
    sans = repondre.repondre_question(corpus, "Quel est le délai de préavis pour rompre un CDI ?", corriger=False)
    assert sans["abstention"] is True
