"""Extraction des références croisées (« l'article 12 du présent code », « الفصل 5 ») du Code du travail.

Pour chaque mention : type (``interne`` au Code, ``externe`` à un autre texte, ``relative`` à
« l'article précédent »), cibles (numéros d'articles, plages développées), portée et position.
Les mentions relatives (« précédent », « suivant ») sont résolues d'après l'article source.

Contrôle automatique : une cible interne dont le numéro de base n'existe pas dans le corpus signale
une référence mal extraite **ou un défaut d'OCR** (ex. « 2779 » pour 279).

Règles à base de motifs, sans apprentissage ; pas de gold humain à ce jour (voir ``RESULTATS.md``).

Usage : python -X utf8 -m src.obligation_extraction.references_croisees
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "reports/platinum/references"

# ------------------------------------------------------------------ français
_SUF_FR = r"(?:\s+(?:bis|ter|quater|quinter|quinquies|sexies))?"
_NUM_FR = rf"\d{{1,4}}(?:\s?-\s?\d{{1,2}})?{_SUF_FR}"
_PAREN = r"(?:\s*\((?:[^()]{0,40})\))?"
_ITEM_FR = rf"{_NUM_FR}{_PAREN}"
_SEP_PLURIEL = r"(?:\s*,\s*|\s+et\s+|\s+ou\s+|\s+à\s+|\s+ainsi que\s+)"
RE_REF_FR = re.compile(
    rf"\b(?P<mot>articles)\s+(?P<liste>{_ITEM_FR}(?:{_SEP_PLURIEL}{_ITEM_FR})*)",
    re.IGNORECASE)
RE_REF_FR_SINGULIER = re.compile(
    rf"\b(?P<mot>article|art\.)\s+(?P<liste>{_ITEM_FR}(?:(?:\s+et\s+|\s+ou\s+|\s+à\s+){_ITEM_FR})*)", re.IGNORECASE)
RE_RELATIF_FR = re.compile(
    r"\b(?:l'|les?\s+|aux?\s+|des?\s+)?(?:(?P<n>deux|trois|quatre|cinq)\s+)?articles?\s+(?P<rel>pr[ée]c[ée]dents?|suivants?|ci-dessus|ci-dessous|ci-apr[èe]s|"
    r"susvis[ée]s?|pr[ée]cit[ée]s?|sus-?indiqu[ée]s?)", re.IGNORECASE)
RE_ET_SUIVANTS = re.compile(r"\s*et\s+suivants?", re.IGNORECASE)
PORTEE_INTERNE_FR = re.compile(r"^\s*(?:du|de|dudit)?\s*(?:pr[ée]sent|ce|cet|cette)\s+"
                               r"(code|chapitre|titre|livre|section|article|paragraphe|alin[ée]a)", re.IGNORECASE)
PORTEE_CODE_FR = re.compile(
    r"^\s*(?:du|de la|de l'|des)\s*(?P<nom>code (?:p[ée]nal|des obligations et des contrats|de proc[ée]dure civile(?: et commerciale)?|"
    r"du travail|de la sécurité sociale|de la nationalité|de commerce|de la fonction publique)|"
    r"loi n?°?\s*[\d-]+[^,;.)]{0,40}|d[ée]cret[^,;.)]{0,40}|arr[êe]t[ée][^,;.)]{0,40}|loi du [^,;.)]{0,30}|constitution)",
    re.IGNORECASE)
RE_CODE_TRAVAIL = re.compile(r"code du travail", re.IGNORECASE)

# ------------------------------------------------------------------ arabe
_NUM_AR = r"\d{1,4}(?:\s?-\s?\d{1,3})?(?:\s+(?:مكرر|ثالثا|رابعا|خامسا|سادسا))?"
_ITEM_AR = rf"{_NUM_AR}(?:\s*\((?:[^()]{{0,40}})\))?"
RE_REF_AR = re.compile(
    rf"(?<![؀-ۿ])[وفبلك]?ال(?P<mot>فصل|فصول|فصلين)\s+(?:من\s+)?(?P<liste>{_ITEM_AR}"
    rf"(?:\s*(?:،|,)\s*{_ITEM_AR}|\s+و\s*{_ITEM_AR}|\s+أو\s+{_ITEM_AR}|\s+إلى\s+{_ITEM_AR}|\s+و{_ITEM_AR})*)")
RE_REF_AR_SANS_AL = re.compile(
    rf"(?<![؀-ۿ])[وفبلك]?(?:ب|ل)?(?P<mot>فصل)\s+(?P<liste>{_ITEM_AR})")
RE_RELATIF_AR = re.compile(r"(?<![؀-ۿ])[وفبلك]?ال(?:فصل)\s+(?P<rel>السابق|الموالي|المتقدم|اللاحق|المشار إليه|المذكور)")
PORTEE_INTERNE_AR = re.compile(r"^\s*(?:من\s+)?(?:هذه|هذا)\s+(المجلة|الباب|القسم|الفصل|الكتاب)")
PORTEE_EXTERNE_AR = re.compile(
    r"^\s*(?:من\s+)?(?:ال)?(مجلة\s+[^\s،.]+(?:\s+[^\s،.]+)?|قانون\s+(?:عدد\s+)?[\d]+[^،.]{0,30}|قانون\s+المؤرخ[^،.]{0,30}|"
    r"قانون\s+(?:الجنائي|الجزائي|التجاري)|أمر[^،.]{0,30})")

TOKEN_NUM = re.compile(r"\d{1,4}(?:\s?-\s?\d{1,3})?(?:\s+(?:bis|ter|quater|quinter|quinquies|sexies|مكرر|ثالثا|رابعا|خامسا|سادسا))?", re.IGNORECASE)
# Intitulé d'article : « Article 21-2 (Ajouté par la loi…).- », « Article 361.- », « الفصل 140 (نقح …).- »
RE_ENTETE = re.compile(
    rf"(?:articles?|الفصل)\s+(?:{_NUM_FR}|{_NUM_AR})\s*(?:\((?:[^()]{{0,300}})\)|\(°)?\s*(?:\.\s*[-–—]|\.\s|[-–—]\s)", re.IGNORECASE)
PLAGE_MAX = 150     # une plage « 53 à 56 » est développée jusqu'à 150 articles (« 7 à 111 » : jours fériés)


def _normaliser_num(t: str) -> str:
    t = re.sub(r"\s*-\s*", "-", t.strip())
    return re.sub(r"\s+", " ", t).lower()


def _base(num: str) -> int:
    return int(re.match(r"\d+", num).group(0))


def _ordre_arabe(num: str) -> str:
    """Dans le texte arabe numérisé, « 94-4 » est souvent écrit « 4-94 » (inversion bidirectionnelle) :
    un numéro composé « a-b » avec a < b est remis dans l'ordre « b-a » (l'indice d'un article « bis »
    numéroté est plus petit que le numéro principal)."""
    m = re.fullmatch(r"(\d{1,3})-(\d{1,3})(\D.*|)", num)
    if m and int(m.group(1)) < int(m.group(2)):
        return f"{m.group(2)}-{m.group(1)}{m.group(3)}"
    return num


def _developper(liste: str, langue: str) -> list[str]:
    """Numéros cités par la liste ; « 53 à 56 » / « 7 إلى 111 » sont développés en plage."""
    sep_plage = r"\s+à\s+" if langue == "fr" else r"\s+إلى\s+"
    morceaux = re.split(sep_plage, liste)
    cibles = []
    for i, morceau in enumerate(morceaux):
        nums = [_normaliser_num(m.group(0)) for m in TOKEN_NUM.finditer(re.sub(r"\([^()]*\)", " ", morceau))]
        if langue == "ar":
            nums = [_ordre_arabe(n) for n in nums]
        if i > 0 and cibles and nums:
            debut, fin = _base(cibles[-1]), _base(nums[0])
            if 0 < fin - debut <= PLAGE_MAX:
                cibles.extend(str(n) for n in range(debut + 1, fin))     # bornes comprises : la fin est ajoutée ci-dessous
        cibles.extend(nums)
    vus, uniques = set(), []
    for c in cibles:
        if c not in vus:
            vus.add(c)
            uniques.append(c)
    return uniques


def _est_en_tete(texte: str, debut: int) -> bool:
    """Vrai si la mention est l'intitulé de l'article (« Article 21-2 (Ajouté par la loi…).- »), pas un renvoi."""
    apres = texte[debut:debut + 160]
    return bool(RE_ENTETE.match(apres))


def _portee(suite: str, langue: str) -> tuple[str, str]:
    """(type, portée) d'après le texte qui suit la liste d'articles."""
    if langue == "fr":
        if PORTEE_INTERNE_FR.match(suite):
            return "interne", PORTEE_INTERNE_FR.match(suite).group(1).lower()
        m = PORTEE_CODE_FR.match(suite)
        if m:
            nom = m.group("nom").strip().lower()
            return ("interne", "code") if RE_CODE_TRAVAIL.search(nom) else ("externe", nom)
    else:
        if PORTEE_INTERNE_AR.match(suite):
            return "interne", PORTEE_INTERNE_AR.match(suite).group(1)
        m = PORTEE_EXTERNE_AR.match(suite)
        if m:
            nom = m.group(1).strip()
            return ("interne", "code") if nom.startswith("مجلة الشغل") else ("externe", nom)
    return "interne", "implicite"


def extraire_references(texte: str, source: int | None = None, langue: str = "fr") -> list[dict]:
    """Références croisées d'un texte d'article. ``source`` = numéro de l'article d'où vient le texte."""
    refs, pris = [], []
    motifs = [(RE_REF_FR, RE_REF_FR_SINGULIER, RE_RELATIF_FR)] if langue == "fr" else [(RE_REF_AR, RE_REF_AR_SANS_AL, RE_RELATIF_AR)]
    multi, simple, relatif = motifs[0]
    for m in sorted(list(multi.finditer(texte)) + list(simple.finditer(texte)) + list(relatif.finditer(texte)), key=lambda x: (x.start(), -x.end())):
        if any(d <= m.start() < f for d, f in pris):
            continue                               # déjà couvert par une mention plus large
        if "rel" not in m.groupdict() and (_est_en_tete(texte, m.start()) or (
                m.start() == 0 and re.match(r"Articles?\s+\d+\s+(?:à|et)\s+\d+\s*(?:\(|\.|-)", texte))):
            continue        # intitulé d'article ou de plage abrogée, pas un renvoi
        if "rel" in m.groupdict():
            cible = []
            rel = m.group("rel").lower()
            n = {"deux": 2, "trois": 3, "quatre": 4, "cinq": 5}.get((m.groupdict().get("n") or "").lower(), 1)
            if source is not None and rel.startswith(("pr", "سابق", "السابق", "المتقدم")):
                if not rel.startswith(("susvis", "précit", "precit", "sus")):
                    cible = [str(k) for k in range(max(1, source - n), source)]
            if source is not None and rel.startswith(("suivant", "الموالي", "اللاحق")):
                cible = [str(k) for k in range(source + 1, source + n + 1)]
            refs.append({"type": "relative", "portee": rel, "cibles": cible, "texte": m.group(0), "debut": m.start(), "fin": m.end()})
            pris.append((m.start(), m.end()))
            continue
        liste = m.group("liste")
        suite = texte[m.end():m.end() + 90].lstrip("° ").replace("°", "")
        if re.match(r"\s*\((?:abrog|ألغ)", suite, re.IGNORECASE):
            continue        # intitulé d'une plage abrogée (« Articles 272 à 277 (Abrogés par la loi… ») : pas un renvoi
        cibles = _developper(liste, langue)
        if not cibles:
            continue
        type_, portee = _portee(suite, langue)
        ref = {"type": type_, "portee": portee, "cibles": cibles, "texte": texte[m.start():m.end()], "debut": m.start(), "fin": m.end()}
        if langue == "fr" and RE_ET_SUIVANTS.match(suite):
            ref["et_suivants"] = True
        refs.append(ref)
        pris.append((m.start(), m.end()))
    return refs


def valider(refs: list[dict], numeros: set[int], abroges: set[int] = frozenset()) -> None:
    """Marque les cibles internes sans article de ce numéro dans le corpus (OCR ou extraction fausse),
    et celles qui visent un article abrogé (renvoi valable mais mort)."""
    for r in refs:
        interne = r["type"] in ("interne", "relative")
        r["inexistantes"] = [c for c in r["cibles"] if interne and _base(c) not in numeros]
        r["abrogees"] = [c for c in r["cibles"] if interne and _base(c) in abroges]


# ------------------------------------------------------------------ corpus
def _lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def traiter(langue: str) -> tuple[list[dict], dict]:
    if langue == "fr":
        lignes = _lire(RACINE / "data/processed/articles_fr_corrige.csv")
        champ_id, champ_texte = "article_id", "texte_fr"
    else:
        corrige = RACINE / "data/processed/articles_ar_corrige.csv"     # défauts d'OCR corrigés, s'il existe
        lignes = _lire(corrige if corrige.exists() else RACINE / "data/processed/articles_ar.csv")
        champ_id, champ_texte = "article_id", "texte_ar"
    numeros = {int(l["numero"]) for l in lignes if str(l["numero"]).isdigit()}
    abroges = {int(l["numero"]) for l in lignes if str(l["numero"]).isdigit()
               and (l.get("abroge", "").lower() == "true" or re.search(r"abrog|ألغي|إلغاء", l[champ_texte][:140], re.IGNORECASE))}
    for l in lignes:                                   # plages abrogées « Article 391 à 396 », « Articles 336 et 337 »
        m = re.match(r"Articles?\s+(\d+)\s+(à|et)\s+(\d+)", l[champ_texte])
        if m:
            deb, fin = int(m.group(1)), int(m.group(3))
            plage = range(deb, fin + 1) if m.group(2) == "à" else (deb, fin)
            numeros |= set(plage)
            if re.search(r"abrog", l[champ_texte][:140], re.IGNORECASE):
                abroges |= set(plage)
    if langue == "ar":                                # les articles abrogés ne sont pas des sources de renvois
        lignes = [l for l in lignes if l.get("abroge", "").lower() != "true"]
    toutes = []
    for l in lignes:
        src = int(l["numero"]) if str(l["numero"]).isdigit() else None
        refs = extraire_references(l[champ_texte], src, langue)
        valider(refs, numeros, abroges)
        for r in refs:
            toutes.append({"source": l[champ_id], "page": l.get("page", ""), "langue": langue, **r})
    interne = [r for r in toutes if r["type"] == "interne"]
    cibles = [c for r in interne for c in r["cibles"]]
    stats = {
        "articles_lus": len(lignes), "mentions": len(toutes),
        "articles_avec_renvoi": len({r["source"] for r in toutes}),
        "par_type": {t: sum(1 for r in toutes if r["type"] == t) for t in ("interne", "externe", "relative")},
        "portee_implicite": sum(1 for r in interne if r["portee"] == "implicite"),
        "cibles_internes": len(cibles), "cibles_sans_article": sum(len(r["inexistantes"]) for r in interne),
        "mentions_avec_cible_inexistante": sum(1 for r in toutes if r["inexistantes"]),
        "cibles_vers_article_abroge": sum(len(r["abrogees"]) for r in interne),
    }
    return toutes, stats


def ecrire(langue: str, toutes: list[dict], sortie: Path) -> None:
    sortie.mkdir(parents=True, exist_ok=True)
    with open(sortie / f"references_{langue}.csv", "w", encoding="utf-8-sig", newline="") as f:
        champs = ["source", "page", "langue", "type", "portee", "cibles", "inexistantes", "abrogees", "texte"]
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        for r in toutes:
            w.writerow({**r, "cibles": " ".join(r["cibles"]), "inexistantes": " ".join(r["inexistantes"]),
                        "abrogees": " ".join(r["abrogees"])})
    with open(sortie / f"graphe_{langue}.csv", "w", encoding="utf-8", newline="") as f:     # arêtes source -> cible
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["source", "cible", "type", "portee"])
        for r in toutes:
            if r["type"] in ("interne", "relative"):
                for c in r["cibles"]:
                    w.writerow([r["source"], c, r["type"], r["portee"]])


def coherence(refs_fr: list[dict], refs_ar: list[dict], sortie: Path) -> dict:
    """Compare les renvois internes d'un article français et de son équivalent arabe (alignement v6).

    Les deux versions devraient renvoyer aux mêmes articles ; une différence signale un défaut d'OCR
    (le plus souvent arabe, ex. « 5 » pour 95) ou une divergence réelle. Liste à vérifier sur l'image."""
    def cibles(refs: list[dict]) -> dict[str, set[int]]:
        par: dict[str, set[int]] = {}
        for r in refs:
            if r["type"] == "interne":
                par.setdefault(r["source"], set()).update(_base(c) for c in r["cibles"])
        return par

    fr, ar = cibles(refs_fr), cibles(refs_ar)
    # Le français regroupe parfois plusieurs articles arabes (« Article 21 » contient 21-2…21-13) :
    # on compare par entrée française, avec l'union des renvois des articles arabes qui lui sont alignés.
    groupes: dict[str, list[str]] = {}
    for a in _lire(RACINE / "data/processed/alignement_fr_ar_v6.csv"):
        if a["statut"] == "apparié":
            groupes.setdefault(a["article_fr"], []).append(a["article_ar"])
    lignes, stats = [], {"entrees_fr_appariees": len(groupes), "avec_renvoi": 0, "identiques": 0, "differentes": 0, "un_seul_cote": 0}
    for f, liste_ar in groupes.items():
        a = " ".join(liste_ar)
        sf, sa = fr.get(f, set()), set().union(*(ar.get(x, set()) for x in liste_ar))
        if not sf and not sa:
            continue
        stats["avec_renvoi"] += 1
        if sf == sa:
            stats["identiques"] += 1
            continue
        stats["un_seul_cote" if not sf or not sa else "differentes"] += 1
        lignes.append({"article_ar": a, "article_fr": f, "cibles_fr": " ".join(map(str, sorted(sf))),
                       "cibles_ar": " ".join(map(str, sorted(sa))), "seulement_fr": " ".join(map(str, sorted(sf - sa))),
                       "seulement_ar": " ".join(map(str, sorted(sa - sf)))})
    with open(sortie / "coherence_ar_fr.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["article_ar", "article_fr", "cibles_fr", "cibles_ar", "seulement_fr", "seulement_ar"])
        w.writeheader()
        w.writerows(lignes)
    stats["taux_identiques"] = round(stats["identiques"] / stats["avec_renvoi"], 3) if stats["avec_renvoi"] else None
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", type=Path, default=SORTIE)
    args = parser.parse_args()
    resume, toutes_langues = {}, {}
    for langue in ("fr", "ar"):
        toutes, stats = traiter(langue)
        ecrire(langue, toutes, args.sortie)
        resume[langue], toutes_langues[langue] = stats, toutes
        print(langue, json.dumps(stats, ensure_ascii=False))
    resume["coherence_ar_fr"] = coherence(toutes_langues["fr"], toutes_langues["ar"], args.sortie)
    print("coherence", json.dumps(resume["coherence_ar_fr"], ensure_ascii=False))
    (args.sortie / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
