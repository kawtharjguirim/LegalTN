"""Tests du pipeline de traitement des questions (src/pipeline/traitement.py), une étape à la fois."""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from src.pipeline import traitement as t  # noqa: E402


@pytest.fixture(scope="module")
def p():
    return t.pipeline()


# 1. langue
def test_detection_langue():
    assert t.detecter_langue("Quel est le préavis ?") == "fr"
    assert t.detecter_langue("ما هي مدة الإعلام بإنهاء عقد الشغل؟") == "ar"
    assert t.detecter_langue("شنوة الحقوق متاع الخدام ؟") == "tunisien"
    assert t.detecter_langue("Chnowa el 7a9 mta3 el khadem ?") == "arabizi"


# 2. translittération
def test_translitteration_arabizi(p):
    assert t.translitterer_mot("5edma") == "خدمة"
    assert t.translitterer_mot("7a9") == "حاق"
    sortie = t.translitterer_arabizi("el congé mta3 5 ayem", p.correcteur.est_mot_francais)
    assert "congé" in sortie            # mot français connu : gardé
    assert "متاع" in sortie
    assert " 5 " in sortie              # nombre : gardé


# 3. mots vides
def test_mots_vides_avant_normalisation_de_ya():
    vides = t.charger_mots_vides()
    assert t.retirer_mots_vides(["على", "علي", "العمل"], vides) == ["علي", "العمل"]


def test_negations_et_modaux_jamais_retires():
    vides = t.charger_mots_vides()
    phrase = ["ne", "peut", "pas", "sans", "sauf", "aucun", "doit", "interdit", "obligatoire",
              "لا", "ليس", "غير", "إلا", "لم", "لن", "يجب", "يمنع", "يجوز"]
    assert t.retirer_mots_vides(phrase, vides) == phrase
    assert not (vides["fr"] & t.PROTEGES_FR) and not (vides["ar"] & t.PROTEGES_AR)


# 4. normalisation
def test_normalisation():
    assert t.normaliser(["Préavis", "إعلام", "مدة", "على", "عَقْدٌ", "الشـغل"]) == \
        ["preavis", "اعلام", "مده", "علي", "عقد", "الشغل"]


# 5. lexiques
def test_lexique_tunisien_et_sigles(p):
    assert p.appliquer_lexiques(["خدمه"]) == ["شغل"]
    assert p.appliquer_lexiques(["preavis", "cdi"]) == ["preavis", "contrat", "duree", "indeterminee"]
    assert p.appliquer_lexiques(["contrat", "cdi"]) == ["contrat", "duree", "indeterminee"]


# 6. racinisation
def test_racinisation_arabe():
    assert t.raciniser_ar(["والعمال", "الشغل", "conge"]) == ["عمال", "شغل", "conge"]


# 7. SymSpell
def test_symspell_sur_jetons_et_mots_vides_exclus(p):
    jetons, corrections = p.corriger_jetons(["preavi", "contart", "14"])
    assert jetons == ["preavis", "contrat", "14"]
    assert len(corrections) == 2
    assert "dans" not in p.correcteur.freq_fr and "pour" not in p.correcteur.freq_fr
    assert p.corriger_jetons(["sousse"], {"sousse"})[0] == ["sousse"]   # nom propre intact


# 8. synonymes
def test_synonymes_par_expansion(p):
    assert p.ajouter_synonymes(["duree", "hebdomadaire"]) == ["duree", "hebdomadaire", "semaine"]
    assert p.ajouter_synonymes(["semaine"]) == ["semaine", "hebdomadaire"]


# chaîne complète et mode debug
def test_mode_debug_renvoie_chaque_etape(p):
    r = p.repondre("quel est le préavi pour un contart CDI ?")
    assert [e["etape"][:2] for e in r["etapes"]] == ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."]
    assert r["question_corrigee"] == "quel est le préavis pour un contrat à durée indéterminée ?"
    assert r["abstention"] is False


def test_hors_perimetre_et_arabe(p):
    assert p.repondre("Quelle est la capitale de la Tunisie ?")["abstention"] is True
    r = p.repondre("ما هي مدة الإعلام بإنهاء عقد الشغل؟")
    assert r["candidats"][0]["article"] == "14 bis"


def test_duree_hebdomadaire_article_79_dans_le_top5(p):
    # Partie C : les synonymes font remonter le 79 du rang 35 au rang 4, mais pas en tête
    # (le 90 contient aussi « normale » et « semaine »). Cas consigné dans les erreurs.
    r = p.repondre("Quelle est la durée légale du travail hebdomadaire ?", k=5)
    assert "79" in [c["article"] for c in r["candidats"]]
