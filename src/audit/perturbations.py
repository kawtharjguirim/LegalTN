"""Perturbations « INV » : transformations d'une question qui ne doivent pas changer la réponse.

Toutes sont déterministes. Les paraphrases, elles, sont écrites à la main
(``data/dev/questions_paraphrases_v1.csv``).
"""

from __future__ import annotations

import re
import unicodedata

POLITESSE = {"fr": "Bonjour, j'aimerais savoir : ", "ar": "السلام عليكم، أريد أن أعرف: "}
RE_PONCTUATION = re.compile(r"[?!.,;:؟،؛«»\"]")


def sans_accents(q: str) -> str:
    return unicodedata.normalize("NFC", "".join(
        c for c in unicodedata.normalize("NFD", q) if unicodedata.category(c) != "Mn"))


def sans_ponctuation(q: str) -> str:
    return " ".join(RE_PONCTUATION.sub(" ", q).split())


def faute_de_frappe(q: str) -> str:
    """Inverse les 2e et 3e lettres du mot le plus long (au moins 5 lettres)."""
    mots = q.split(" ")
    k = max(range(len(mots)), key=lambda i: (len(mots[i]), -i))
    m = mots[k]
    if len(m) < 5 or not m[1:3].isalpha():
        return q
    mots[k] = m[0] + m[2] + m[1] + m[3:]
    return " ".join(mots)


def politesse(q: str, langue: str) -> str:
    if langue == "fr":
        return POLITESSE["fr"] + q[0].lower() + q[1:]
    return POLITESSE["ar"] + q


def normalisation_alef(q: str) -> str:
    """Écriture arabe courante sans hamza sur l'alif (أ إ آ -> ا)."""
    return re.sub("[أإآ]", "ا", q)


def variantes(q: str, langue: str, dans_perimetre: bool) -> dict[str, str]:
    """Variantes INV d'une question. Hors périmètre : on vérifie seulement que l'abstention
    résiste à une formule de politesse et à une faute de frappe."""
    lg = "ar" if langue.startswith("ar") else "fr"
    v = {"politesse": politesse(q, lg), "faute_de_frappe": faute_de_frappe(q)}
    if dans_perimetre:
        v["sans_ponctuation"] = sans_ponctuation(q)
        if lg == "fr":
            v["sans_accents"] = sans_accents(q)
            v["minuscules"] = q.lower()
        else:
            v["normalisation_alef"] = normalisation_alef(q)
    # Une variante identique à l'original n'apporte rien.
    return {nom: t for nom, t in v.items() if t != q}
