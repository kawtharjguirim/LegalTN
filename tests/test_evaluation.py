"""Tests de fumée des scripts d'évaluation et de la démo LegalTN.

Ces tests ne lancent AUCUNE mesure sur un jeu gelé (data/test_locked/).
Ils vérifient seulement :
- que les jeux gelés n'ont pas été modifiés (sha256 consignés dans experiments.md) ;
- que les corpus ont la taille attendue ;
- que les fonctions de normalisation et de repérage des articles se comportent comme prévu ;
- que la démo cite l'article attendu ou s'abstient, et qu'un cas limite connu reste documenté.

Lancer depuis la racine du projet : python3 -m pytest
"""
import hashlib
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
sys.path.insert(0, str(RACINE / "src" / "demo"))

import baseline_bm25 as bm  # noqa: E402
import repondre  # noqa: E402

# sha256 des jeux gelés, tels que consignés dans experiments.md.
HASHES_GELES = {
    "questions_reference_v2.csv": "0015db2c03d552eb281abf3b6a7230d62bf2164b145b626c898bdbbe65388083",
    "ocr_candidats_v1.csv": "0969c1aa98193fb40c1c8d9989f3fa4599ec072f4e9eab3448b5d0a7fc927608",
    "ocr_baseline_v1.csv": "f2be31a94d64886b313ec5a41f1d9dbcfc396d8a42126c1585417f2301cb59d3",
}


def sha256(chemin):
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def corpus():
    return repondre.charger()


def test_jeux_geles_inchanges():
    for nom, attendu in HASHES_GELES.items():
        chemin = RACINE / "data" / "test_locked" / nom
        assert chemin.exists(), f"jeu gelé absent : {nom}"
        assert sha256(chemin) == attendu, f"jeu gelé modifié : {nom}"


def test_tailles_des_corpus():
    assert len(bm.lire(bm.FR)) == 498
    assert len(bm.lire(bm.AR)) == 515


def test_intitule_article_fr():
    assert bm.intitule_fr("Article 14 bis. (Ajouté par la loi n° 94-29)") == "14 bis"
    assert bm.intitule_fr("Article 6.-") == "6"
    assert bm.intitule_fr("Texte sans numéro d'article") is None


def test_tokens_fr_retire_les_mots_vides():
    jetons = bm.tokens("Le préavis de rupture du contrat", "fr")
    assert "preavis" in jetons
    assert "rupture" in jetons
    assert "le" not in jetons
    assert "de" not in jetons


def test_demo_s_abstient_hors_perimetre(corpus):
    resultat = corpus["fr"].repondre("Quelle est la capitale de la Tunisie ?")
    assert resultat["abstention"] is True


def test_demo_cite_l_article_14_bis(corpus):
    resultat = corpus["fr"].repondre(
        "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"
    )
    assert resultat["abstention"] is False
    assert resultat["candidats"][0]["article"] == "14 bis"


@pytest.mark.xfail(
    strict=True,
    reason="Limite connue : le sigle « CDI » n'est pas dans le corpus ; la démo s'abstient à tort. "
           "strict=True : le test échouera si ce cas est corrigé, pour rappeler de mettre à jour la démo.",
)
def test_demo_sigle_cdi_devrait_repondre(corpus):
    resultat = corpus["fr"].repondre("Quel est le délai de préavis pour rompre un CDI ?")
    assert resultat["abstention"] is False
