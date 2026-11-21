"""Traduction d'une question en tunisien (arabizi) par le LLM local, vers le français ou l'arabe
standard. Les exemples du prompt sont inventés et absents des jeux d'évaluation.
Les traductions sont mises en cache (``runs/cache_traductions.json``).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.rag import generer

RACINE = Path(__file__).resolve().parents[2]
CACHE = RACINE / "runs/cache_traductions.json"

CONSIGNES = {
    "fr": ("Tu traduis des questions écrites en dialecte tunisien (derja), souvent en lettres latines "
           "avec des chiffres (3 = ع, 7 = ح, 9 = ق, 5 = خ). Traduis la question en français clair, "
           "avec le vocabulaire du droit du travail. Réponds uniquement par la traduction."),
    "ar": ("أنت تترجم أسئلة مكتوبة باللهجة التونسية، غالبا بحروف لاتينية مع أرقام (3 = ع، 7 = ح، 9 = ق، 5 = خ). "
           "ترجم السؤال إلى العربية الفصحى بمصطلحات قانون الشغل. أجب بالترجمة فقط."),
}
EXEMPLES = {
    "fr": [("Ken el patron ma khalasnich, chnowa na3mel ?", "Que faire si l'employeur ne me paie pas ?"),
           ("3andi 7a9 fi congé maladie ?", "Ai-je droit à un congé de maladie ?")],
    "ar": [("Ken el patron ma khalasnich, chnowa na3mel ?", "ماذا أفعل إذا لم يدفع لي المؤجر أجري؟"),
           ("3andi 7a9 fi congé maladie ?", "هل لي الحق في عطلة مرض؟")],
}


def _lire_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


LEXIQUE = RACINE / "data/tunisien/lexique_derja_fr.csv"


def _lire_lexique() -> list[tuple[str, str]]:
    """Paires (mot derja, équivalent français) du lexique, dont le statut n'est pas « rejeté »."""
    import csv
    try:
        with LEXIQUE.open(encoding="utf-8", newline="") as f:
            lignes = list(csv.DictReader(f))
    except OSError:
        return []
    return [(r["derja"], r["francais"]) for r in lignes if r.get("statut") != "rejete"]


def glossaire(question: str) -> list[tuple[str, str]]:
    """Entrées du lexique présentes dans la question (mots entiers, insensible à la casse)."""
    import re
    texte = " " + " ".join(re.findall(r"[a-z0-9']+", question.lower())) + " "
    return [(d, f) for d, f in _lire_lexique() if f" {d} " in texte]


def traduire(question: str, cible: str = "fr", modele: str = generer.MODELE_DEFAUT) -> str:
    gloss = glossaire(question) if cible == "fr" else []
    signature = "|".join(f"{d}={f}" for d, f in gloss)
    cache = _lire_cache()
    cle = f"{modele}|{cible}|{signature}|{question}"
    if cle in cache:
        return cache[cle]
    consigne = CONSIGNES[cible]
    if gloss:
        consigne += ("\nLexique à respecter (dialecte → français) : "
                     + "; ".join(f"« {d} » = {f}" for d, f in gloss) + ".")
    messages = [{"role": "system", "content": consigne}]
    for q, t in EXEMPLES[cible]:
        messages += [{"role": "user", "content": q}, {"role": "assistant", "content": t}]
    messages.append({"role": "user", "content": question})
    texte = generer.appeler(messages, modele).strip().strip('"«» ').split("\n")[0]
    cache[cle] = texte
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return texte
