"""Extraction d'obligations par règles sur le corpus français du Code du travail.

Règles alignées sur ``data/dev/obligations_guide_annotation_v1.md`` :
trois modaux (obligation, interdiction, permission), un rôle ``qui`` copié
tel qu'écrit, l'action ``quoi`` issue de la proposition modalisée et la
condition ``quand`` si le texte la précise.

Les sorties sont des *prédictions automatiques* : elles ne remplacent pas
l'annotation humaine et ne doivent jamais être copiées dans le modèle gold.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

INTERDICTION = [
    r"il est interdit\b",
    r"il leur est interdit\b",
    r"il lui est interdit\b",
    r"est interdit[es]?\b",
    r"sont interdit[es]?\b",
    r"il est d[eé]fendu\b",
    r"d[eé]fense est faite\b",
    r"nul ne peut\b",
    r"ne peu(?:vent|t|x)\b",
    r"ne doi(?:vent|t)\b",
    r"ne saura(?:ient|it)\b",
    r"ne peu(?:vent|t) pas\b",
    r"pas autoris[eé][es]?\b",
    r"n'est pas permis\b",
]
OBLIGATION = [
    r"est tenue? de\b",
    r"sont tenus de\b",
    r"sont tenues de\b",
    r"a l'obligation de\b",
    r"ont l'obligation de\b",
    r"il incombe\b",
    r"incombe\b",
    r"doi(?:vent|t)\b",
    r"devr(?:ont|a)\b",
    r"obligatoire\b",
    r"est charg[eé][es]? de\b",
    r"redevable\b",
    r"astreint[es]?\b",
    r"est tenu\b",
]
PERMISSION = [
    r"a la facult[eé] de\b",
    r"ont la facult[eé] de\b",
    r"peu(?:vent|t)\b",
    r"est autoris[eé][es]?\b",
    r"sont autoris[eé][es]?\b",
    r"est libre de\b",
    r"est dispens[eé][es]?\b",
    r"a le droit de\b",
    r"ont le droit de\b",
]
MODAUX = (
    [("interdiction", p) for p in INTERDICTION]
    + [("obligation", p) for p in OBLIGATION]
    + [("permission", p) for p in PERMISSION]
)

NON_OBLIGATION = [
    r"^on entend par\b",
    r"^l'expression\b",
    r"^est dite?\b",
    r"^sont dites?\b",
    r"^au sens de\b",
    r"^pour l'application de\b",
]

ROLES = [
    "le secr\u00e9taire d'etat", "les secr\u00e9taires d'etat",
    "la caisse nationale de s\u00e9curit\u00e9 sociale",
    "la caisse nationale", "l'inspection du travail",
    "l'inspecteur du travail", "le contr\u00f4leur du travail",
    "le chef d'entreprise", "le ma\u00eetre d'apprentissage",
    "les conseillers prud'hommes", "le conseiller prud'homme",
    "les employeurs", "l'employeur", "les salari\u00e9s", "le salari\u00e9",
    "les travailleurs", "le travailleur", "les apprentis", "l'apprenti",
    "les ma\u00eetres", "le ma\u00eetre", "le tribunal", "le greffier",
    "le ministre", "le syndicat", "les syndicats",
    "les repr\u00e9sentants", "le repr\u00e9sentant", "la commission",
    "le conseil", "le bureau", "l'entreprise", "les entreprises",
    "l'entrepreneur", "les entrepreneurs", "l'ouvrier", "les ouvriers",
    "l'agent", "les agents", "l'employ\u00e9", "les employ\u00e9s",
    "le personnel", "les parties", "toute personne", "chaque partie",
    "l'adjudicataire", "le demandeur", "le requ\u00e9rant",
]

CONDITIONS = [
    r"\b(lorsque|quand|sauf si|si|dans le cas|en cas de|au cours de|avant|apr\u00e8s|"
    r"dans les conditions|\u00e0 partir|au plus tard|au plus t\u00f4t|pendant|durant|"
    r"\u00e0 condition que|d\u00e8s|dans un d\u00e9lai|dans le d\u00e9lai)\b[^,.;:]*",
]
RE_CONDITION = re.compile("|".join(CONDITIONS), re.IGNORECASE)
RE_MODAUX = [(m, re.compile(p, re.IGNORECASE)) for m, p in MODAUX]
RE_NON_OBL = [re.compile(p, re.IGNORECASE) for p in NON_OBLIGATION]
RE_ARTICLE_TETE = re.compile(r"^Article\s+[\d\s\w\u00e9\u00e8\u00ea'\u2019.-]+[.:\u2014-]\s*", re.IGNORECASE)


def _sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    ).lower()


def _roles_normalises() -> list[tuple[str, str]]:
    paires = [(_sans_accents(r), r) for r in ROLES]
    return sorted(paires, key=lambda t: len(t[0]), reverse=True)


_ROLES = _roles_normalises()


def trouver_modal(phrase: str) -> tuple[str, re.Match] | tuple[None, None]:
    """Premier marqueur modal par position ; priorité au plus tôt dans la phrase."""
    meilleur: tuple[int, str, re.Match] | None = None
    for modal, rx in RE_MODAUX:
        for match in rx.finditer(phrase):
            if meilleur is None or match.start() < meilleur[0]:
                meilleur = (match.start(), modal, match)
                break
    if meilleur is None:
        return None, None
    return meilleur[1], meilleur[2]


def trouver_qui(phrase: str, avant: int) -> str:
    """Rôle explicite le plus proche avant le marqueur modal, sinon après."""
    normalise = _sans_accents(phrase)
    candidat, distance = "", 10**9
    for norm, role in _ROLES:
        debut = 0
        while True:
            pos = normalise.find(norm, debut)
            if pos < 0:
                break
            borne_g = pos == 0 or not normalise[pos - 1].isalnum()
            borne_d = pos + len(norm) >= len(normalise) or not normalise[
                pos + len(norm)].isalnum()
            if borne_g and borne_d and pos < avant and avant - pos < distance:
                candidat = phrase[pos:pos + len(norm)]
                distance = avant - pos
            debut = pos + 1
    if candidat:
        return candidat
    for norm, _ in _ROLES:
        pos = normalise.find(norm, avant)
        if pos >= 0:
            borne_g = pos == 0 or not normalise[pos - 1].isalnum()
            borne_d = pos + len(norm) >= len(normalise) or not normalise[
                pos + len(norm)].isalnum()
            if borne_g and borne_d:
                return phrase[pos:pos + len(norm)]
    return ""


def extraire_quoi(phrase: str, fin_marqueur: int) -> str:
    """Action = fin de la proposition modalisée (jusqu'à la coupure suivante)."""
    reste = phrase[fin_marqueur:]
    coupure = re.search(r"[,;:.]\s", reste)
    if coupure:
        reste = reste[:coupure.start()]
    return reste.strip(" .;:")


def extraire_quand(phrase: str) -> str:
    match = RE_CONDITION.search(phrase)
    return match.group(0).strip() if match else ""


def est_definition(phrase: str) -> bool:
    tete = RE_ARTICLE_TETE.sub("", phrase.strip())
    return any(rx.match(tete) for rx in RE_NON_OBL)


def analyser_phrase(phrase: str) -> dict:
    """Analyse une phrase candidate ; ``est_obligation_predite`` vaut False
    pour les définitions et les phrases sans marqueur modal."""
    modal, match = trouver_modal(phrase)
    if modal is None or est_definition(phrase):
        return {
            "est_obligation_predite": False, "modal_predit": "",
            "qui_predit": "", "quoi_predit": "", "quand_predit": "",
        }
    return {
        "est_obligation_predite": True,
        "modal_predit": modal,
        "qui_predit": trouver_qui(phrase, match.start()),
        "quoi_predit": extraire_quoi(phrase, match.end()),
        "quand_predit": extraire_quand(phrase),
    }


def extraire_depuis_csv(candidats: Path, sortie: Path) -> int:
    """Écrit un CSV de prédictions à partir d'un lot de candidats.

    Le modèle gold (``obligations_modele_v1.csv``) n'est jamais lu ni écrit.
    """
    with open(candidats, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f))
    champs = ["obligation_id", "article_fr", "page_fr", "phrase",
              "est_obligation_predite", "modal_predit", "qui_predit",
              "quoi_predit", "quand_predit"]
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for lig in lignes:
            analyse = analyser_phrase(lig["phrase"])
            w.writerow({
                "obligation_id": lig["obligation_id"],
                "article_fr": lig["article_fr"],
                "page_fr": lig["page_fr"],
                "phrase": lig["phrase"],
                "est_obligation_predite": str(analyse["est_obligation_predite"]),
                "modal_predit": analyse["modal_predit"],
                "qui_predit": analyse["qui_predit"],
                "quoi_predit": analyse["quoi_predit"],
                "quand_predit": analyse["quand_predit"],
            })
    return len(lignes)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidats", type=Path,
                        default=Path("data/dev/obligations_candidats_dev_v1.csv"))
    parser.add_argument("--sortie", type=Path,
                        default=Path("data/dev/obligations_predictions_dev_v1.csv"))
    args = parser.parse_args()
    n = extraire_depuis_csv(args.candidats, args.sortie)
    print(f"{n} phrases analysées -> {args.sortie}")
