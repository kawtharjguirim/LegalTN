"""Étiquettes de domaine des articles du Code du travail, tirées de la **structure du Code** (livres,
titres, chapitres) et non d'une annotation : aucune étiquette n'est posée par un modèle ni à la main
article par article.

Source des bornes : les intitulés de chapitres que le texte français place en fin d'article (« … Chapitre
III Fin du contrat de travail » à la fin de l'article 13 ouvre le chapitre qui commence à l'article 14), recoupés
avec la hiérarchie arabe de ``articles_ar.csv`` (colonne ``chapitre``). Les 12 domaines regroupent les
chapitres voisins ; ce regroupement est une décision de conception. ``verifier_bornes`` mesure combien de
bornes sont confirmées par un intitulé français et par un changement de chapitre arabe.

Un article est étiqueté par son **numéro de base** (« 21-2 » et « 21 bis » comptent comme 21), donc l'article
français et son équivalent arabe ont la même étiquette.

Usage : python -X utf8 -m src.domaine.etiquettes
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]

# (premier article, dernier article, domaine). Les plages abrogées (272–277, 391–396) restent dans leur chapitre
# mais leurs articles sont exclus du jeu (texte « abrogé », sans contenu).
PLAGES = [
    (1, 30, "contrat_de_travail"),
    (31, 52, "conventions_collectives"),
    (53, 78, "conditions_et_protection_du_travail"),
    (79, 133, "duree_repos_conges"),
    (134, 151, "salaire"),
    (152, 156, "hygiene_securite_sante"),
    (157, 169, "representation_du_personnel"),
    (170, 182, "inspection_et_sanctions"),
    (183, 232, "conflits_et_juridictions"),
    (233, 241, "inspection_et_sanctions"),
    (242, 257, "syndicats"),
    (258, 288, "emploi_et_formation"),
    (289, 334, "hygiene_securite_sante"),
    (335, 337, "conflits_et_juridictions"),
    (338, 369, "emploi_et_formation"),
    (370, 375, "conditions_et_protection_du_travail"),
    (376, 396, "conflits_et_juridictions"),
    (397, 446, "statuts_particuliers"),
]
DOMAINES = sorted({d for _, _, d in PLAGES})

# Intitulé numéroté en tête (« Article 14 bis (Ajouté par la loi n° 94-29 du 21 février 1994).- », « الفصل 5 مكرر (أضيف …).- ») :
# jusqu'au premier « .- » s'il apparaît dans les 260 premiers caractères.
RE_ENTETE_FR = re.compile(r"^\s*(?:Articles?|ARTICLES?)\s.{0,260}?\.\s*[-–—]", re.DOTALL)
RE_ENTETE_AR = re.compile(r"^\s*(?:ال)?فصل\s.{0,260}?\.\s*[-–—]", re.DOTALL)
# Intitulé de structure en fin d'article : il nomme le chapitre suivant (ce serait une fuite de l'étiquette).
RE_STRUCTURE_FR = re.compile(r"\s(?:LIVRE|Livre|TITRE|Titre|CHAPITRE|Chapitre|SECTION|Section)\s+(?:[IVXLC1l]+|[Pp]remier|unique|UNIQUE|\d+)\b.*$", re.DOTALL)
RE_STRUCTURE_AR = re.compile(r"\s(?:الكتاب|العنوان|الباب|القسم|الجزء|الفرع)\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|وحيد|\S+)\s*[—\-–:.]?\s.*$", re.DOTALL)
RE_REF_NUM = re.compile(r"((?:articles?|art\.|الفصول|الفصلين|الفصل)\s+(?:de\s+)?)(?:\d+(?:\s?-\s?\d+)?(?:\s+(?:bis|ter|quater|quinter|مكرر|ثالثا|رابعا))?)(?:(?:\s*,\s*|\s+et\s+|\s+à\s+|\s+و\s*|\s+إلى\s+)\d+(?:\s?-\s?\d+)?)*", re.IGNORECASE)


def domaine_de(numero: int) -> str | None:
    for debut, fin, d in PLAGES:
        if debut <= numero <= fin:
            return d
    return None


def nettoyer(texte: str, langue: str) -> str:
    """Texte de l'article sans son intitulé numéroté, sans l'intitulé de structure final, sans numéros d'articles cités."""
    t = (RE_ENTETE_FR if langue == "fr" else RE_ENTETE_AR).sub("", texte, count=1)
    t = (RE_STRUCTURE_FR if langue == "fr" else RE_STRUCTURE_AR).sub("", t)
    t = RE_REF_NUM.sub(lambda m: m.group(1) + "N", t)
    return " ".join(t.split())


def _lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def charger(langue: str) -> list[dict]:
    """Articles étiquetés d'une langue : numero, id, texte nettoyé, domaine. Les articles abrogés sont exclus."""
    if langue == "fr":
        lignes = _lire(RACINE / "data/processed/articles_fr_corrige.csv")
        champ = "texte_fr"
    else:
        lignes = _lire(RACINE / "data/processed/articles_ar.csv")
        champ = "texte_ar"
    sortie = []
    for l in lignes:
        if not str(l["numero"]).isdigit():
            continue
        n = int(l["numero"])
        brut = l[champ]
        if l.get("abroge", "").lower() == "true" or re.search(r"abrog|ألغي", brut[:150], re.IGNORECASE):
            continue
        d = domaine_de(n)
        texte = nettoyer(brut, langue)
        if d is None or len(texte) < 40:
            continue
        sortie.append({"id": l["article_id"], "numero": n, "langue": langue, "domaine": d, "texte": texte, "longueur": len(texte)})
    return sortie


def verifier_bornes() -> dict:
    """Pour chaque début de plage : un intitulé de structure français en fin d'article précédent ? un changement
    de chapitre arabe ? Mesure la solidité des bornes, pas celle du regroupement en domaines."""
    fr = {int(l["numero"]): l["texte_fr"] for l in _lire(RACINE / "data/processed/articles_fr_corrige.csv") if str(l["numero"]).isdigit()}
    ar_chap: dict[int, set[str]] = {}
    for l in _lire(RACINE / "data/processed/articles_ar.csv"):
        if str(l["numero"]).isdigit():
            ar_chap.setdefault(int(l["numero"]), set()).add(l["chapitre"].split(" > ")[0] + (" > " + l["chapitre"].split(" > ")[1] if " > " in l["chapitre"] else ""))
    lignes, bornes = [], 0
    for (_, fin, d1), (debut, _, d2) in zip(PLAGES, PLAGES[1:]):
        precedent = max((n for n in fr if n < debut), default=None)
        txt = fr.get(precedent, "")
        heading = bool(RE_STRUCTURE_FR.search(txt[30:])) if txt else False
        avant = ar_chap.get(max((n for n in ar_chap if n < debut), default=-1), set())
        apres = ar_chap.get(debut, set())
        chap_ar = bool(avant and apres and avant != apres)
        lignes.append({"debut": debut, "de": d1, "vers": d2, "intitule_fr": heading, "changement_chapitre_ar": chap_ar})
        bornes += 1
    return {"bornes": bornes, "confirmees_fr": sum(l["intitule_fr"] for l in lignes),
            "confirmees_ar": sum(l["changement_chapitre_ar"] for l in lignes),
            "confirmees_au_moins_une": sum(l["intitule_fr"] or l["changement_chapitre_ar"] for l in lignes),
            "aucune": [l["debut"] for l in lignes if not (l["intitule_fr"] or l["changement_chapitre_ar"])], "detail": lignes}


def main() -> None:
    for langue in ("fr", "ar"):
        a = charger(langue)
        c = Counter(x["domaine"] for x in a)
        print(langue, len(a), "articles ; domaines :", dict(sorted(c.items(), key=lambda kv: -kv[1])))
    v = verifier_bornes()
    print({k: v[k] for k in v if k != "detail"})


if __name__ == "__main__":
    main()
