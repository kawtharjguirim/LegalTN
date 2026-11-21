import csv

from src.corpus import corriger_arabe as ca


def test_chaque_correction_trouve_sa_chaine_une_seule_fois():
    originaux = {l["article_id"]: l["texte_ar"] for l in ca.lire(ca.ORIGINE)}
    for c in ca.lire(ca.CORRECTIONS):
        assert originaux[c["article_ar"]].count(c["avant"]) == 1, c
        assert c["verification"] in ("image", "francais") and c["justification"]


def test_application_ne_touche_pas_a_l_original(tmp_path):
    avant = ca.ORIGINE.read_bytes()
    bilan = ca.appliquer(sortie=tmp_path / "corrige.csv")
    assert ca.ORIGINE.read_bytes() == avant
    assert bilan["corrections"] == bilan["image"] + bilan["francais"] >= 20
    corrige = {l["article_id"]: l["texte_ar"] for l in ca.lire(tmp_path / "corrige.csv")}
    assert "مدة 30 يوما" in corrige["AR-64"] and "بما قدره 15 يوما" in corrige["AR-64"]      # congé de maternité
    assert "75 %" in corrige["AR-90"] and "29675" not in corrige["AR-90"]                     # taux des heures supplémentaires
    assert "288 دينارا" in corrige["AR-425"] and "2858" not in corrige["AR-425"]
    assert "ظرف 3 أشهر" in corrige["AR-351"]
    assert "234 و235 و236 و237" in corrige["AR-94-14"]


def test_le_fichier_corrige_existe_et_est_celui_du_moteur():
    from src.evaluation import baseline_bm25
    assert ca.SORTIE.exists() and baseline_bm25.AR.name == "articles_ar_corrige.csv"
