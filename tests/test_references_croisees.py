from src.obligation_extraction.references_croisees import (_ordre_arabe, extraire_references as x, valider)


def cibles(texte, source=50, langue="fr"):
    return [(r["type"], r["cibles"]) for r in x(texte, source, langue)]


def test_renvoi_simple_et_portee():
    r = x("prévues à l'article 21 du présent code", 22)
    assert r[0]["type"] == "interne" and r[0]["portee"] == "code" and r[0]["cibles"] == ["21"]
    assert x("réprimé par l'article 301 du Code Pénal", 251)[0]["type"] == "externe"
    assert x("l'article 2 de la loi n° 60-18 du 27 juillet 1960", 4)[0]["type"] == "externe"


def test_listes_et_plages():
    assert cibles("les articles 234, 236 et 237 du présent code") == [("interne", ["234", "236", "237"])]
    assert cibles("aux articles 53 à 56 du présent code")[0][1] == ["53", "54", "55", "56"]
    assert cibles("articles 67 (paragraphe a) et 68 (paragraphes a et b)")[0][1] == ["67", "68"]
    assert cibles("l'article 234 bis et l'article 94-4")[0][1] == ["234 bis"]


def test_singulier_ne_prend_pas_un_nombre_voisin():
    assert cibles("prévue à l'article 15, 20 jours de salaire") == [("interne", ["15"])]


def test_intitule_n_est_pas_un_renvoi():
    assert x("Article 21-2 (Ajouté par la loi n° 96-62 du 15 juillet 1996).- Cette lettre", 21) == []
    long = "Article 234 (Modifié par la loi n° 69-16 du 27 mars 1969, puis par la loi n° 94-29 du 21 février 1994, et par la loi n° 96-62 du 15 juillet 1996).- Sont punis"
    assert x(long, 234) == []
    assert x("Articles 272 à 277 (Abrogés par la loi n° 96-62)", 271) == []
    assert cibles("Article 361.- Dans les entreprises visées à l'article 338 du présent chapitre", 361) == [("interne", ["338"])]


def test_relatifs_resolus_d_apres_la_source():
    assert cibles("à l'article précédent", 10) == [("relative", ["9"])]
    assert cibles("à l'article suivant", 10) == [("relative", ["11"])]
    assert cibles("aux trois articles précédents", 105) == [("relative", ["102", "103", "104"])]
    assert cibles("l'article ci-dessus", 10) == [("relative", [])]


def test_arabe():
    assert cibles("بالفصل 109 أثناء", 111, "ar") == [("interne", ["109"])]
    assert cibles("الفصلين 278 و280 من هذه المجلة", 286, "ar") == [("interne", ["278", "280"])]
    assert cibles("الفصول 346 إلى 358", 363, "ar")[0][1][0] == "346" and len(cibles("الفصول 346 إلى 358", 363, "ar")[0][1]) == 13
    assert cibles("الفصل السابق", 38, "ar") == [("relative", ["37"])]
    assert x("الفصل 254 من القانون الجنائي", 173, "ar")[0]["type"] == "externe"
    assert x("الفصل 23 من المجلة الجزائية", 30, "ar")[0]["type"] == "externe"


def test_ordre_inverse_des_numeros_composes_arabes():
    assert _ordre_arabe("4-94") == "94-4" and _ordre_arabe("94-4") == "94-4" and _ordre_arabe("21-2") == "21-2"
    assert cibles("الفصل 2-154 من هذه المجلة", 154, "ar") == [("interne", ["154-2"])]
    assert cibles("الفصل 3-68", 70, "ar") == [("interne", ["68-3"])]


def test_validation_inexistantes_et_abrogees():
    refs = x("les articles 14 et 9999 du présent code", 20)
    valider(refs, {14, 20}, {14})
    assert refs[0]["inexistantes"] == ["9999"] and refs[0]["abrogees"] == ["14"]
