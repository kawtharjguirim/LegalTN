import http.client
import threading

import api
from src.rapports import tableau_de_bord as td


def test_page_contient_les_blocs_et_les_chiffres_des_rapports():
    page = td.construire()
    for titre in ("Synthèse", "Validation humaine", "Alignement", "Audit", "Abstention calibrée", "Obligations", "LLM-juge", "Références croisées"):
        assert titre in page
    assert "Référence Claude, non relue" in page and "Référence humaine" in page
    audit = td.json_(td.R / "gold/audit/audit_resultats.json")
    assert td.f(audit["invariance"]["paraphrase"]["decision"]) in page       # chiffre lu dans le JSON, pas écrit à la main
    assert "<svg" in page                                                     # courbe risque-couverture
    assert "Résultat non disponible" not in page


def test_resultat_absent_est_signale(monkeypatch, tmp_path):
    monkeypatch.setattr(td, "R", tmp_path)
    page = td.bloc_audit()
    assert "Résultat non disponible" in page and "src.audit.audit" in page


def test_formats():
    assert td.f(0.5) == "0,500" and td.f(None) == "–" and td.f("", 2) == "–"
    assert "mal" in td.barre("x", 0.1, classe="mal") and "–" in td.barre("x", None)


def test_route_de_l_api():
    td.SORTIE.write_text(td.construire(), encoding="utf-8")
    serveur = api.creer_serveur(port=0)
    t = threading.Thread(target=serveur.serve_forever, daemon=True)
    t.start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", serveur.server_port, timeout=10)
        c.request("GET", "/tableau-de-bord")
        r = c.getresponse()
        corps = r.read().decode("utf-8")
        assert r.status == 200 and "text/html" in r.getheader("Content-Type") and "Tableau de bord d'évaluation" in corps
    finally:
        serveur.shutdown()
        serveur.server_close()
        t.join(timeout=5)
