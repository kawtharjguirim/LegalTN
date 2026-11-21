import re

from src.domaine import etiquettes as et
from src.domaine.evaluer import BLOC, PLIS, plis


def test_plages_sans_chevauchement_et_domaines():
    plages = sorted(et.PLAGES)
    for (_, fin, _), (debut, _, _) in zip(plages, plages[1:]):
        assert fin < debut
    assert len(et.DOMAINES) == 12
    assert et.domaine_de(1) == "contrat_de_travail" and et.domaine_de(95) == "duree_repos_conges"
    assert et.domaine_de(250) == "syndicats" and et.domaine_de(234) == "inspection_et_sanctions"
    assert et.domaine_de(274) == "emploi_et_formation" and et.domaine_de(9999) is None   # 274 : abrogé mais dans son chapitre


def test_bornes_confirmees_par_la_structure_du_code():
    v = et.verifier_bornes()
    assert v["bornes"] == 17 and v["aucune"] == []                    # chaque borne a un intitulé français ou un changement de chapitre arabe
    assert v["confirmees_fr"] == 17 and v["confirmees_ar"] >= 14


def test_nettoyage_supprime_numero_en_tete_structure_finale_et_numeros_cites():
    t = "Article 14 bis (Ajouté par la loi n° 94-29 du 21 février 1994).- L'employeur est tenu, selon les articles 234, 236 et 237 et l'article 21. Chapitre III Fin du contrat de travail"
    n = et.nettoyer(t, "fr")
    assert n == "L'employeur est tenu, selon les articles N et l'article N."
    a = et.nettoyer("الفصل 94 - 6 (أضيف بالقانون عدد 62 لسنة 1996).- طبق الفصل 52 و53", "ar")
    assert a == "طبق الفصل N" and "94" not in a


def test_aucune_fuite_d_intitule_dans_les_textes_charges():
    for langue in ("fr", "ar"):
        articles = et.charger(langue)
        assert len(articles) > 400
        assert {a["domaine"] for a in articles} == set(et.DOMAINES)
        fuite = [a["numero"] for a in articles if re.search(r"\b(?:LIVRE|TITRE|Chapitre)\s+(?:[IVX]+|Premier)\b", a["texte"]) and langue == "fr"]
        assert len(fuite) <= 3                                          # quelques intitulés mal formés par l'OCR peuvent subsister
        assert not [a for a in articles if a["numero"] in (274, 393)]   # plages abrogées exclues


def test_plis_par_blocs_communs_aux_deux_langues():
    numeros = list(range(1, 447))
    for graine in (0, 1, 2):
        p = plis(numeros, graine)
        assert set(p.values()) == set(range(PLIS))
        assert p[10 // BLOC] == p[11 // BLOC]                          # deux articles voisins ne sont jamais séparés
