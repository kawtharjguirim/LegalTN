"""Tests de la pré-annotation NER par règles (fixtures écrites pour les tests)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ner_juridique.pre_annoter import decouper
from src.ner_juridique.regles import annoter, depuis_texte, lisible, vers_texte


def entites(phrase, langue):
    return [(phrase[d:f], t) for d, f, t in annoter(phrase, langue)]


def test_fr_role_institution_delai_montant():
    p = ("L'employeur doit informer l'inspection du travail dans un délai de quinze jours "
         "et verser 300 dinars.")
    assert entites(p, "fr") == [
        ("L'employeur", "ROLE"), ("l'inspection du travail", "INSTITUTION"),
        ("dans un délai de quinze jours", "DELAI"), ("300 dinars", "MONTANT"),
    ]


def test_fr_heures_sont_un_montant():
    assert entites("La durée est de 48 heures par semaine.", "fr") == [
        ("48 heures par semaine", "MONTANT")]


def test_fr_institution_longue_prioritaire():
    p = "après consultation des organisations professionnelles d'employeurs et de travailleurs."
    assert entites(p, "fr") == [
        ("des organisations professionnelles d'employeurs et de travailleurs", "INSTITUTION")]


def test_ar_proclitique_hors_entite():
    p = "يعلم رئيس المؤسسة تفقدية الشغل وللمؤجر أجل خمسة عشر يوما."
    assert entites(p, "ar") == [
        ("رئيس المؤسسة", "ROLE"), ("تفقدية الشغل", "INSTITUTION"),
        # « وللمؤجر » : proclitiques « ول » exclus, article assimilé « ل » conservé.
        ("لمؤجر", "ROLE"), ("أجل خمسة عشر يوما", "DELAI"),
    ]


def test_ar_duel_et_montant():
    p = "يمكن تداركها في الشهرين المواليين وتدفع غرامة قدرها 100 دينار."
    assert entites(p, "ar") == [("في الشهرين المواليين", "DELAI"), ("100 دينار", "MONTANT")]


def test_ar_pas_de_faux_role_sur_wala():
    assert entites("ولا تمنح أية رخصة.", "ar") == []


def test_sans_chevauchement():
    p = "Le secrétaire d'Etat aux affaires sociales, après avis de l'employeur."
    spans = annoter(p, "fr")
    for (d1, f1, _), (d2, f2, _) in zip(spans, spans[1:]):
        assert f1 <= d2


def test_format_aller_retour():
    e = [(0, 11, "ROLE"), (20, 30, "DELAI")]
    assert depuis_texte(vers_texte(e)) == e
    assert depuis_texte("") == []
    with pytest.raises(ValueError):
        depuis_texte("0|3|PER")


def test_lisible():
    assert lisible("L'employeur paie.", [(0, 11, "ROLE")]) == "[L'employeur]ROLE paie."


def test_decoupage_fr_protege_abreviations():
    assert decouper("Voir la loi n°. 12. Le salarié signe; Il part.", "fr") == [
        "Voir la loi n°. 12.", "Le salarié signe;", "Il part."]


def test_decoupage_ar():
    assert decouper("الجملة الأولى. الجملة الثانية؛ الثالثة", "ar") == [
        "الجملة الأولى.", "الجملة الثانية؛", "الثالثة"]
