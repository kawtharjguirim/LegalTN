"""Chargement des corpus, des paires gold et préparation des textes à encoder.

Identifiants :
- côté AR, ``article_id`` (unique, ex. ``AR-6-4``) ;
- côté FR, l'index de ligne ``fr_ligne`` dans ``articles_fr_corrige.csv``
  (les ``article_id`` FR ne sont pas uniques).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
AR = RACINE / "data/processed/articles_ar.csv"
FR = RACINE / "data/processed/articles_fr_corrige.csv"
ALIGNEMENT_NUMEROTATION = RACINE / "data/processed/alignement_fr_ar_v6.csv"
GOLD_DEV = [
    RACINE / "data/dev/alignement_dev_v1.csv",
    RACINE / "data/dev/alignement_dev_v2_a_annoter.csv",
]

# Intitulé en tête d'article : « Article 14 bis.- », « Article premier.- », « الفصل 6 مكرر.- ».
RE_ENTETE_FR = re.compile(
    r"^\s*Article\s+(?:premier|\d+)(?:\s*(?:bis|ter|quater|quinquies|\(?nouveau\)?))*"
    r"\s*(?:\([^)]{0,200}\))?\s*[.:]?\s*[-–—]?\s*",
    re.IGNORECASE,
)
RE_ENTETE_AR = re.compile(
    # « الفصول 272 إلى 277 » (plages abrogées) et « الفصل7 74 » (bruit OCR) inclus.
    r"^\s*الفصو?ل\s*(?:الأول|[\d ]+)(?:\s*إلى\s*\d+)?(?:\s*(?:مكرر|ثالثا|رابعا|خامسا|\(جديد\)))*"
    r"\s*(?:\([^)]{0,200}\))?\s*[.:]?\s*[-–—]?\s*"
)
RE_NUMERO_FR = re.compile(r"^\s*Article\s+(premier|\d+)", re.IGNORECASE)
RE_NUMERO_AR = re.compile(r"^\s*الفصل\s+(الأول|\d+)")


def lire(chemin: Path) -> pd.DataFrame:
    return pd.read_csv(chemin, encoding="utf-8-sig")


def corpus() -> tuple[pd.DataFrame, pd.DataFrame]:
    ar = lire(AR).reset_index(drop=True)
    fr = lire(FR).reset_index(drop=True)
    ar["texte_ar"] = ar["texte_ar"].fillna("")
    fr["texte_fr"] = fr["texte_fr"].fillna("")
    return ar, fr


def paires_gold() -> pd.DataFrame:
    """160 paires vérifiées sur image : colonnes article_ar, fr_ligne, source."""
    lots = []
    for chemin in GOLD_DEV:
        d = lire(chemin)
        verdict = "verdict_image" if "verdict_image" in d else "verdict_auteure"
        d = d[d[verdict].astype(str).str.startswith("correct")]
        lots.append(pd.DataFrame({
            "article_ar": d["article_ar"], "fr_ligne": d["fr_ligne"].astype(int),
            "source": chemin.stem,
        }))
    return pd.concat(lots, ignore_index=True)


def paires_numerotation() -> pd.DataFrame:
    """Sortie du pipeline Bronze (numérotation) : 494 paires « apparié »."""
    d = lire(ALIGNEMENT_NUMEROTATION)
    d = d[d["statut"] == "apparié"].dropna(subset=["fr_ligne"])
    return pd.DataFrame({"article_ar": d["article_ar"], "fr_ligne": d["fr_ligne"].astype(int)})


def numero_fr(texte: str) -> int | None:
    m = RE_NUMERO_FR.match(texte or "")
    if not m:
        return None
    return 1 if m.group(1).lower() == "premier" else int(m.group(1))


def numero_ar(texte: str) -> int | None:
    m = RE_NUMERO_AR.match(texte or "")
    if not m:
        return None
    return 1 if m.group(1) == "الأول" else int(m.group(1))


def normaliser_ar(s: str) -> str:
    """Retire diacritiques et tatweel, unifie alif/ya/ta marbuta (comme la baseline BM25)."""
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("ـ", "")
    s = re.sub("[إأآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return unicodedata.normalize("NFC", s)


def preparer(textes: list[str], langue: str, variante: str) -> list[str]:
    """Variantes de normalisation (ablation) :

    - ``brut`` : texte tel quel, intitulé numéroté compris ;
    - ``sans_entete`` : intitulé retiré, pour que le modèle ne s'appuie pas sur le numéro ;
    - ``sans_entete_norm`` : idem + normalisation orthographique arabe.
    """
    if variante not in {"brut", "sans_entete", "sans_entete_norm"}:
        raise ValueError(f"variante inconnue : {variante}")
    sortie = []
    for t in textes:
        t = " ".join((t or "").split())
        if variante != "brut":
            t = (RE_ENTETE_AR if langue == "ar" else RE_ENTETE_FR).sub("", t, count=1)
        if variante == "sans_entete_norm" and langue == "ar":
            t = normaliser_ar(t)
        sortie.append(t.strip())
    return sortie
