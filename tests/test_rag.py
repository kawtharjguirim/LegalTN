"""Tests du RAG sans appel au LLM : analyse des sorties, citations, garde-fou, prompts."""
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "src" / "demo"))

from rag import rag  # noqa: E402

PASSAGES = [{"article": "14 bis", "fr": "Le préavis..."}, {"article": "14", "fr": "..."}]


def test_articles_dans_texte_fr_et_ar():
    assert rag.articles_dans_texte("Selon l'article 14 bis et l'Article 23.") == ["14 bis", "23"]
    assert rag.articles_dans_texte("حسب الفصل 14 مكرر") == ["14 bis"]


def test_normaliser_article():
    assert rag.normaliser_article("Article 14 BIS") == "14 bis"
    assert rag.normaliser_article(23) == "23"
    assert rag.normaliser_article("n'importe quoi") is None


def test_analyser_json_valide():
    brut = json.dumps({"reponse": "r", "articles_cites": ["article 14 bis"], "extrait": "e", "abstention": False})
    s = rag.analyser("P2", brut)
    assert s["articles_cites"] == ["14 bis"] and s["json_valide"] is True


def test_analyser_json_invalide_ne_plante_pas():
    s = rag.analyser("P2", "pas du json, article 5")
    assert s["json_valide"] is False and s["articles_cites"] == ["5"]


def test_verification_rejette_citation_non_fournie():
    s = rag.verifier_citations({"reponse": "x", "articles_cites": ["99"], "extrait": "", "abstention": False}, PASSAGES)
    assert s["abstention"] is True and s["rejet"].startswith("citation_non_fournie")


def test_verification_rejette_absence_de_citation():
    s = rag.verifier_citations({"reponse": "x", "articles_cites": [], "extrait": "", "abstention": False}, PASSAGES)
    assert s["abstention"] is True and s["rejet"] == "aucune_citation"


def test_verification_garde_citation_fournie():
    s = rag.verifier_citations({"reponse": "x", "articles_cites": ["14 bis"], "extrait": "", "abstention": False}, PASSAGES)
    assert s["abstention"] is False and s["rejet"] is None


def test_p0_ne_recoit_aucun_passage():
    m = rag.construire_messages("P0", "q", PASSAGES)
    assert all("Articles fournis" not in x["content"] for x in m)


def test_p3_contient_les_exemples():
    ex = [{"question": "qe", "passages": PASSAGES, "sortie": {"abstention": True}}]
    m = rag.construire_messages("P3", "q", PASSAGES, ex)
    assert [x["role"] for x in m] == ["system", "user", "assistant", "user"]
