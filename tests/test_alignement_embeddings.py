"""Tests de l'alignement par embeddings : préparation des textes et appariement.

Aucun modèle n'est chargé : les matrices de similarité sont synthétiques.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.alignement_embeddings import donnees as d
from src.alignement_embeddings.aligner import apparier, bonus_numerotation
from src.alignement_embeddings.evaluer import metriques_appariement, metriques_classement


@pytest.mark.parametrize("texte, attendu", [
    ("Article 14 bis.- Le préavis est notifié.", "Le préavis est notifié."),
    ("Article premier.- Le présent code s'applique.", "Le présent code s'applique."),
    ("Article 21 (Modifié par la loi n° 96-62 du 15 juillet 1996).- Ce délai.", "Ce délai."),
])
def test_entete_fr_retire(texte, attendu):
    assert d.preparer([texte], "fr", "sans_entete") == [attendu]


@pytest.mark.parametrize("texte, attendu", [
    ("الفصل 6 مكرر.- يعتبر العامل", "يعتبر العامل"),
    ("الفصل الأول.- تنطبق أحكام", "تنطبق أحكام"),
    ("الفصل7 74.- يتمتع الأطفال", "يتمتع الأطفال"),
    ("الفصول 272 إلى 277 (ألغيت بالقانون عدد 62)", ""),
])
def test_entete_ar_retire(texte, attendu):
    assert d.preparer([texte], "ar", "sans_entete") == [attendu]


def test_variante_brut_conserve_entete():
    assert d.preparer(["Article 3.-  Texte"], "fr", "brut") == ["Article 3.- Texte"]


def test_normalisation_ar():
    # Comme la baseline BM25 : la décomposition NFD retire aussi la hamza (ؤ -> و).
    assert d.preparer(["الفصل 1.- إِلى المؤسسةِ"], "ar", "sans_entete_norm") == ["الي الموسسه"]


def test_variante_inconnue():
    with pytest.raises(ValueError):
        d.preparer(["x"], "fr", "autre")


def test_numeros():
    assert d.numero_fr("Article premier.- x") == 1
    assert d.numero_fr("Article 14 bis.- x") == 14
    assert d.numero_ar("الفصل الأول.- x") == 1
    assert d.numero_ar("الفصل 230.- x") == 230
    assert d.numero_ar("نص بلا عنوان") is None


def test_bonus_numerotation():
    b = bonus_numerotation([1, 2, None], [2, 1, None])
    assert b.tolist() == [[0, 1, 0], [1, 0, 0], [0, 0, 0]]


SIM = np.array([
    [0.9, 0.8, 0.1],
    [0.85, 0.2, 0.1],
    [0.1, 0.1, 0.3],
])


def test_argmax_autorise_doublons():
    assert apparier(SIM, "argmax") == {0: 0, 1: 0, 2: 2}


def test_mutuel_garde_couples_reciproques():
    assert apparier(SIM, "mutuel") == {0: 0, 2: 2}


def test_hongrois_un_pour_un():
    assert apparier(SIM, "hongrois") == {0: 1, 1: 0, 2: 2}


def test_seuil_abstention():
    assert apparier(SIM, "hongrois", seuil=0.5) == {0: 1, 1: 0}


def test_metriques():
    gold_i, gold_j = np.array([0, 1]), np.array([0, 0])
    m = metriques_classement(SIM, gold_i, gold_j)
    assert m["p_at_1"] == 1.0 and m["mrr"] == 1.0
    a = metriques_appariement({0: 1, 1: 0}, {0: 0, 1: 0}, {0: 0, 1: 0, 2: 2})
    assert a["precision_gold"] == 0.5 and a["rappel_gold"] == 0.5
    assert a["accord_numerotation_rappel"] == pytest.approx(1 / 3)


def test_gold_coherent_avec_corpus():
    ar, fr = d.corpus()
    gold = d.paires_gold()
    assert len(gold) == 160
    assert set(gold["article_ar"]) <= set(ar["article_id"])
    assert gold["fr_ligne"].between(0, len(fr) - 1).all()
