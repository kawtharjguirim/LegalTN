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


def traduire(question: str, cible: str = "fr", modele: str = generer.MODELE_DEFAUT) -> str:
    cache = _lire_cache()
    cle = f"{modele}|{cible}|{question}"
    if cle in cache:
        return cache[cle]
    messages = [{"role": "system", "content": CONSIGNES[cible]}]
    for q, t in EXEMPLES[cible]:
        messages += [{"role": "user", "content": q}, {"role": "assistant", "content": t}]
    messages.append({"role": "user", "content": question})
    texte = generer.appeler(messages, modele).strip().strip('"«» ').split("\n")[0]
    cache[cle] = texte
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return texte
