"""Extraction des nombres d'un article, en chiffres et en toutes lettres (français, arabe).

Sert à repérer une divergence juridique concrète : un délai, un montant, un âge ou un renvoi
qui n'est pas le même dans les deux versions.
"""

from __future__ import annotations

import re
import unicodedata

UNITES_FR = {"zero": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6,
             "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13,
             "quatorze": 14, "quinze": 15, "seize": 16, "vingt": 20, "vingts": 20, "trente": 30,
             "quarante": 40, "cinquante": 50, "soixante": 60}
MULT_FR = {"cent": 100, "cents": 100, "mille": 1000}

UNITES_AR = {"واحد": 1, "واحدة": 1, "احد": 1, "اثنان": 2, "اثنين": 2, "اثنا": 2, "اثني": 2,
             "ثلاث": 3, "ثلاثة": 3, "اربع": 4, "اربعة": 4, "خمس": 5, "خمسة": 5, "ست": 6, "ستة": 6,
             "سبع": 7, "سبعة": 7, "ثمان": 8, "ثماني": 8, "ثمانية": 8, "تسع": 9, "تسعة": 9,
             "عشر": 10, "عشرة": 10, "عشرون": 20, "عشرين": 20, "ثلاثون": 30, "ثلاثين": 30,
             "اربعون": 40, "اربعين": 40, "خمسون": 50, "خمسين": 50, "ستون": 60, "ستين": 60,
             "سبعون": 70, "سبعين": 70, "ثمانون": 80, "ثمانين": 80, "تسعون": 90, "تسعين": 90,
             "مائة": 100, "مئة": 100, "مائتي": 200, "مائتين": 200, "الف": 1000, "الاف": 1000,
             # ordinaux employés pour les âges (« دون الثامنة عشرة »)
             "السادسة": 6, "الثامنة": 8, "الرابعة": 4, "الخامسة": 5, "العاشرة": 10}
DUELS_AR = ("يومين", "شهرين", "سنتين", "عامين", "اسبوعين", "ساعتين")


def _sans_signes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


# Clés normalisées comme les textes (« مائة » -> « مايه » une fois la hamza retirée).
UNITES_AR = {_sans_signes(k): v for k, v in UNITES_AR.items()}
MULT_AR = {_sans_signes(k) for k in ("الف", "الاف", "مائة", "مئة")}
RE_CHIFFRES = re.compile(r"\d+(?:[.,]\d+)?")
CHIFFRES_INDIENS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _sans_accents(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def nombres_fr(texte: str) -> set[int]:
    t = _sans_accents(texte.lower()).replace("-", " ")
    sortie = {int(float(x.replace(",", "."))) for x in RE_CHIFFRES.findall(t)}
    mots = re.findall(r"[a-z]+", t)
    courant, vu = 0, False
    for k, m in enumerate(mots + ["."]):
        if m in UNITES_FR:
            v = UNITES_FR[m]
            # « quatre vingt » = 80 ; « soixante dix » = 70
            courant = courant * v if (m in ("vingt", "vingts") and courant == 4) else courant + v
            vu = True
        elif m in MULT_FR and vu:
            courant = max(courant, 1) * MULT_FR[m]
        elif m == "et" and vu:
            continue
        else:
            if vu and courant:
                sortie.add(courant)
            courant, vu = 0, False
    return sortie


def nombres_ar(texte: str) -> set[int]:
    t = re.sub("[إأآ]", "ا", texte.translate(CHIFFRES_INDIENS))
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    sortie = {int(float(x.replace(",", "."))) for x in RE_CHIFFRES.findall(t)}
    mots = re.findall(r"[؀-ۿ]+", t)
    courant, vu = 0, False
    for m in mots + ["."]:
        base = m[1:] if m.startswith("و") and m[1:] in UNITES_AR else m       # « وعشرين »
        base = base[2:] if base.startswith("ال") and base[2:] in UNITES_AR else base
        if base in MULT_AR and vu and courant:
            courant *= UNITES_AR[base]                  # « خمسة آلاف » = 5000
        elif base in UNITES_AR:
            courant, vu = courant + UNITES_AR[base], True
        else:
            if vu and courant:
                sortie.add(courant)
            courant, vu = 0, False
            if any(m.endswith(d) for d in DUELS_AR):
                sortie.add(2)
    return sortie
