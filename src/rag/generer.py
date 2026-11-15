"""Génération avec un LLM ouvert local (Ollama) : réponse citée et résumé en langage clair.

Trois stratégies de prompting (ablation) :
- ``zero_shot``      : consignes seules ;
- ``few_shot``       : consignes + deux exemples (FR et AR) écrits pour ce projet ;
- ``citation_forcee``: few-shot + format imposé « [Article N] » vérifié après coup ;
  une réponse sans citation valide est remplacée par l'abstention.

Le LLM ne voit que les articles retrouvés : il ne peut citer que ceux-là. Une citation
d'un article absent du contexte est comptée comme hallucination de citation.

Prérequis : Ollama installé et ``ollama pull qwen2.5:3b``.
"""

from __future__ import annotations

import re

MODELE_DEFAUT = "qwen2.5:3b"
STRATEGIES = ("zero_shot", "few_shot", "citation_forcee")
ABSTENTION = {
    "fr": "Je ne trouve pas de réponse dans les articles du Code du travail fournis.",
    "ar": "لم أجد إجابة في فصول مجلة الشغل المقدمة.",
}
AVERTISSEMENT = {
    "fr": "Information juridique générale, pas un conseil juridique.",
    "ar": "معلومة قانونية عامة وليست استشارة قانونية.",
}

CONSIGNES = {
    "fr": (
        "Tu es un assistant qui répond à partir du Code du travail tunisien UNIQUEMENT. "
        "Utilise seulement les articles fournis ci-dessous. Réponds en français, en 1 à 3 phrases, "
        "et cite l'article utilisé sous la forme [Article N]. Si les articles ne contiennent pas "
        f"la réponse, réponds exactement : « {ABSTENTION['fr']} » N'invente jamais d'article."
    ),
    "ar": (
        "أنت مساعد يجيب اعتمادا على مجلة الشغل التونسية فقط. استعمل الفصول المقدمة أدناه دون غيرها. "
        "أجب بالعربية في جملة إلى ثلاث جمل واذكر الفصل المعتمد بالصيغة [Article N]. "
        f"إذا لم تتضمن الفصول الإجابة فأجب حرفيا: «{ABSTENTION['ar']}» ولا تختلق أي فصل."
    ),
}
EXEMPLES = [
    ("Quel est le délai de préavis pour un contrat à durée indéterminée ?",
     "[Article 14] Le préavis de rupture du contrat de travail à durée indéterminée est d'un mois ...",
     "Le préavis est d'un mois [Article 14]."),
    ("ما هي مدة الإعلام بالفسخ في عقد الشغل غير محدد المدة؟",
     "[Article 14] يكون الإعلام بفسخ عقد الشغل غير محدد المدة قبل شهر ...",
     "مدة الإعلام شهر واحد [Article 14]."),
]
RE_CITATION = re.compile(r"\[Article\s+(\d+(?:\s+(?:bis|ter|quater))?)\]", re.IGNORECASE)


def contexte(resultats, max_car: int = 1200) -> str:
    return "\n\n".join(f"[Article {r.article}] {' '.join(r.texte.split())[:max_car]}" for r in resultats)


def construire_prompt(question: str, resultats, langue: str, strategie: str) -> list[dict]:
    lg = "ar" if langue == "ar" else "fr"
    messages = [{"role": "system", "content": CONSIGNES[lg]}]
    if strategie in {"few_shot", "citation_forcee"}:
        for q, ctx, rep in EXEMPLES:
            messages += [{"role": "user", "content": f"Articles :\n{ctx}\n\nQuestion : {q}"},
                         {"role": "assistant", "content": rep}]
    messages.append({"role": "user", "content": f"Articles :\n{contexte(resultats)}\n\nQuestion : {question}"})
    return messages


def citations(texte: str) -> list[str]:
    return [" ".join(c.lower().split()) for c in RE_CITATION.findall(texte)]


def client(timeout: float = 120.0):
    import ollama

    return ollama.Client(timeout=timeout)  # hôte : variable OLLAMA_HOST, sinon 127.0.0.1:11434


def disponible(modele: str = MODELE_DEFAUT) -> bool:
    """Vrai si le serveur Ollama répond et que le modèle est téléchargé."""
    try:
        noms = {m.model for m in client(timeout=2).list().models}
    except Exception:
        return False
    return modele in noms or f"{modele}:latest" in noms


def appeler(messages: list[dict], modele: str = MODELE_DEFAUT, graine: int = 0) -> str:
    rep = client().chat(model=modele, messages=messages,
                        options={"temperature": 0.0, "seed": graine, "num_ctx": 4096})
    return rep["message"]["content"].strip()


def repondre(question: str, resultats, langue: str, strategie: str = "citation_forcee",
             modele: str = MODELE_DEFAUT, graine: int = 0) -> dict:
    lg = "ar" if langue == "ar" else "fr"
    if not resultats:
        return {"reponse": ABSTENTION[lg], "citations": [], "abstention": True, "brut": ""}
    brut = appeler(construire_prompt(question, resultats, langue, strategie), modele, graine)
    cites = citations(brut)
    autorises = {r.article.lower() for r in resultats}
    abstention = ABSTENTION[lg][:25] in brut
    reponse = brut
    if strategie == "citation_forcee" and not abstention and (
            not cites or any(c not in autorises for c in cites)):
        reponse, abstention = ABSTENTION[lg], True
    return {"reponse": reponse, "citations": cites, "abstention": abstention, "brut": brut,
            "citations_hors_contexte": [c for c in cites if c not in autorises]}


def resumer(article: str, texte: str, langue: str, modele: str = MODELE_DEFAUT) -> str:
    """Résumé en langage clair d'un article (2 à 4 phrases), sans ajout d'information."""
    lg = "ar" if langue == "ar" else "fr"
    consigne = (
        "Résume cet article du Code du travail tunisien en langage clair, en 2 à 4 phrases courtes, "
        "pour un non-juriste. N'ajoute aucune information absente du texte."
        if lg == "fr" else
        "لخص هذا الفصل من مجلة الشغل التونسية بلغة واضحة في جملتين إلى أربع جمل قصيرة لغير المختص "
        "ولا تضف أي معلومة غير موجودة في النص."
    )
    return appeler([{"role": "system", "content": consigne},
                    {"role": "user", "content": f"[Article {article}] {' '.join(texte.split())}"}], modele)
