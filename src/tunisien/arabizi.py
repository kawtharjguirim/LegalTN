"""Détection du tunisien en arabizi et translittération par règles vers l'écriture arabe.

L'arabizi note l'arabe en lettres latines, avec des chiffres pour les sons sans équivalent
(3 = ع, 7 = ح, 9 = ق, 5 = خ, 2 = ء). La translittération est volontairement simple : c'est la
baseline « par règles » de la comparaison ; les mots français mêlés à la phrase (« congé »,
« patron ») sont translittérés eux aussi, ce qui fait partie de la difficulté mesurée.
"""

from __future__ import annotations

import re

# Mots outils et verbes très fréquents du tunisien écrit en latin.
LEXIQUE = set("""ken kenet chnowa chnoua chnouwa chkoun chkon kifech kifeh 9adech 9adeh ch7al
qadech najem najjem tnajem ynajem najmou nekhou nekhdem lazem lezem mta3 mte3 3andi 3andou 3and
bech wala walla mouch mech barcha 7a9 fel fil mel bel lel 3al 3la ama ba3d 9bal elli illi tawa
khedma khedmet 5edma patron chrika chehriya chehriti flous youm ayem jem3a chhar se3a wa9t
ya3mel na3mel ykhalsouni ykhalsouhom""".split())
RE_CHIFFRE_DANS_MOT = re.compile(r"[a-z][2356789]|[2356789][a-z]", re.IGNORECASE)
RE_ARABE = re.compile(r"[؀-ۿ]")


def est_tunisien(question: str) -> bool:
    """Arabizi : écriture latine, et chiffre collé à une lettre (« 7a9 ») ou au moins deux
    mots du lexique tunisien."""
    if RE_ARABE.search(question):
        return False
    mots = re.findall(r"[a-z0-9']+", question.lower())
    if any(RE_CHIFFRE_DANS_MOT.search(m) and not m.isdigit() for m in mots):
        return True
    return sum(m in LEXIQUE for m in mots) >= 2


# ---------------------------------------------------------------- translittération
PREFIXES = [("wel", "وال"), ("fel", "في ال"), ("fil", "في ال"), ("mel", "من ال"), ("bel", "بال"),
            ("lel", "لل"), ("3al", "على ال"), ("el", "ال"), ("il", "ال"), ("l", "ال")]
DIGRAPHES = [("ch", "ش"), ("sh", "ش"), ("kh", "خ"), ("gh", "غ"), ("th", "ث"), ("dh", "ض"),
             ("ou", "و"), ("ow", "و"), ("oo", "و"), ("aa", "ا"), ("ee", "ي"), ("ii", "ي")]
LETTRES = {"2": "ء", "3": "ع", "5": "خ", "6": "ط", "7": "ح", "8": "غ", "9": "ق",
           "b": "ب", "p": "ب", "t": "ت", "j": "ج", "d": "د", "r": "ر", "z": "ز", "s": "س",
           "f": "ف", "v": "ف", "q": "ق", "k": "ك", "c": "ك", "g": "ق", "l": "ل", "m": "م",
           "n": "ن", "h": "ه", "w": "و", "y": "ي", "x": "كس", "i": "ي", "o": "و", "u": "و"}


def _mot(m: str) -> str:
    if m.isdigit():
        return m                       # « 5 ayem » : un nombre reste un nombre
    sortie, k = "", 0
    while k < len(m):
        bi = m[k:k + 2]
        trouve = next((a for b, a in DIGRAPHES if bi == b), None)
        if trouve:
            sortie, k = sortie + trouve, k + 2
            continue
        c = m[k]
        if c in "ae":
            if k == 0:
                sortie += "ا"
            elif k == len(m) - 1 and c == "a":
                sortie += "ة"            # « khedma » -> « خدمة »
            # a et e au milieu du mot : voyelles brèves, non écrites (« 3andi » -> « عندي ») ;
            # une voyelle longue s'écrit doublée (« aa »), traitée par les digraphes.
        elif c in LETTRES:
            sortie += LETTRES[c]
        k += 1
    # Lettres répétées par la transcription (« iya » -> « يي ») : une seule.
    return re.sub(r"(.)\1+", r"\1", sortie)


def translitterer(question: str) -> str:
    """Arabizi -> écriture arabe, mot à mot ; l'article « el » est soudé au mot suivant."""
    mots = re.findall(r"[a-z0-9']+|\?", question.lower().replace("’", "'"))
    sortie, prefixe = [], ""
    for m in mots:
        if m == "?":
            sortie.append("؟")
            continue
        m = m.split("'")[-1]          # « d'essai » -> « essai »
        if m in dict(PREFIXES):
            prefixe = dict(PREFIXES)[m]
            continue
        mot = _mot(m)
        if prefixe:
            mot = prefixe + (mot[1:] if mot.startswith("ا") and prefixe.endswith("ال") else mot)
            prefixe = ""
        sortie.append(mot)
    return " ".join(sortie).replace(" ؟", "؟")
