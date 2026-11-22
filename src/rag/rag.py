"""RAG contrôlé sur le Code du travail : récupération BM25 -> LLM ouvert local -> vérification des citations.

Variantes de prompting comparées (voir src/evaluation/evaluer_rag.py) :
  P0  LLM seul, aucun passage fourni (baseline négative : mesure les articles inventés)
  P1  RAG, consignes en zéro-shot, réponse libre
  P2  RAG, sortie JSON imposée + règle d'abstention explicite
  P3  P2 + deux exemples (few-shot) tirés du dev ; ces exemples sont exclus de l'évaluation
  P2V P2 + vérification : toute citation absente des passages fournis -> abstention

Le LLM tourne en local via Ollama (http://127.0.0.1:11434), température 0 et graine fixe.
Aucune API payante, aucune donnée envoyée à l'extérieur. Bibliothèque standard uniquement.

Usage :
  python -X utf8 src/rag/rag.py "Quel est le préavis pour rompre un CDI ?"
  python -X utf8 src/rag/rag.py --variante P1 "..."
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src"))

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODELE_DEFAUT = "qwen2.5:3b"
GRAINE = 2026
K_PASSAGES = 3
MAX_CARACTERES = 1500  # par texte d'article, pour tenir dans le contexte d'un petit modèle
NUM_CTX = 8192      # le prompt few-shot (P3) dépasse le contexte par défaut d'Ollama
NUM_PREDICT = 400   # borne la longueur de sortie (évite les générations sans fin)
VARIANTES =["P0", "P1", "P2", "P3", "P2V"]
MOTIF_ARTICLE = re.compile(r"\b(?:article|art\.)\s*(\d+)(?:\s*(bis|ter|quater))?", re.IGNORECASE)
MOTIF_ARTICLE_AR = re.compile(r"الفصل\s*(\d+)(?:\s*(مكرر))?")
MESSAGE_ABSTENTION = ("Je ne dispose pas d'une source suffisante dans le Code du travail pour répondre "
                      "de manière fiable à cette question.")
MESSAGE_ABSTENTION_AR = "لا أملك مصدرا كافيا في مجلة الشغل للإجابة عن هذا السؤال بشكل موثوق."
ARABE = re.compile(r"[؀-ۿ]")


def message_abstention(question):
    """Message d'abstention dans l'écriture de la question (arabe ou latine)."""
    return MESSAGE_ABSTENTION_AR if ARABE.search(str(question)) else MESSAGE_ABSTENTION

SYSTEME_BASE = (
    "Tu es un assistant d'information sur le Code du travail tunisien. "
    "Tu ne donnes pas de conseil juridique personnalisé. "
    "Réponds dans la langue de la question."
)
CONSIGNES_RAG = (
    "Réponds UNIQUEMENT à partir des articles fournis. N'invente jamais de numéro d'article. "
    "Cite le numéro de chaque article utilisé sous la forme « article N »."
)
CONSIGNES_JSON = (
    "Si les articles fournis ne permettent pas de répondre, ou si la question ne porte pas sur le droit "
    "du travail, mets \"abstention\": true et laisse \"articles_cites\" vide. "
    "Réponds uniquement par un objet JSON de la forme : "
    "{\"reponse\": \"...\", \"articles_cites\": [\"N\"], \"extrait\": \"phrase recopiée de l'article\", "
    "\"abstention\": false}"
)


# ---------------------------------------------------------------- récupération des passages
K_HYBRIDE = 5  # Gold : passages de la recherche hybride (BM25 + e5, RRF), voir experiments.md 22/11/2026


def _textes(labels, corpus):
    textes = {l: {} for l in labels}
    for lg in ("fr", "ar"):
        for a in corpus[lg].articles:
            if a["article"] in textes and lg not in textes[a["article"]]:
                textes[a["article"]][lg] = a["texte"]
    return [{"article": l, **textes[l]} for l in labels]


def passages_hybrides(question, corpus, index, k=K_HYBRIDE):
    """Top-k de la fusion RRF (BM25 langue détectée + encodeur e5 croisé), textes FR et AR."""
    import repondre
    from retrieval.hybride import classement_bm25, fusion_rrf
    langue = repondre.detecter_langue(question)
    bm = classement_bm25(corpus[langue], question)
    dense = [lab for lab, _ in index.classer(question)]
    return _textes([lab for lab, _ in fusion_rrf([bm, dense])][:k], corpus)


def passages_bm25(question, corpus, k=K_PASSAGES):
    """Top-k articles BM25 (langue détectée, sans seuil), avec textes FR et AR quand ils existent."""
    import repondre
    from retrieval.hybride import classement_bm25
    langue = repondre.detecter_langue(question)
    labels = classement_bm25(corpus[langue], question)[:k]
    textes = {l: {} for l in labels}
    for lg in ("fr", "ar"):
        for a in corpus[lg].articles:
            if a["article"] in textes and lg not in textes[a["article"]]:
                textes[a["article"]][lg] = a["texte"]
    return [{"article": l, **textes[l]} for l in labels]


# ---------------------------------------------------------------- prompts
def formater_passages(passages):
    blocs = []
    for p in passages:
        bloc = [f"[Article {p['article']}]"]
        if p.get("fr"):
            bloc.append("FR : " + p["fr"][:MAX_CARACTERES])
        if p.get("ar"):
            bloc.append("AR : " + p["ar"][:MAX_CARACTERES])
        blocs.append("\n".join(bloc))
    return "\n\n".join(blocs) if blocs else "(aucun article retrouvé)"


def construire_messages(variante, question, passages, exemples=()):
    if variante == "P0":
        return [{"role": "system", "content": SYSTEME_BASE + " Cite les articles du Code sur lesquels tu t'appuies."},
                {"role": "user", "content": question}]
    systeme = SYSTEME_BASE + " " + CONSIGNES_RAG
    if variante in ("P2", "P2V", "P3"):
        systeme += " " + CONSIGNES_JSON
    messages = [{"role": "system", "content": systeme}]
    if variante == "P3":
        for ex in exemples:
            messages.append({"role": "user", "content": _contenu_utilisateur(ex["question"], ex["passages"])})
            messages.append({"role": "assistant", "content": json.dumps(ex["sortie"], ensure_ascii=False)})
    messages.append({"role": "user", "content": _contenu_utilisateur(question, passages)})
    return messages


def _contenu_utilisateur(question, passages):
    return f"Articles fournis :\n{formater_passages(passages)}\n\nQuestion : {question}"


# ---------------------------------------------------------------- appel et analyse
def appeler_llm(messages, modele=MODELE_DEFAUT, json_impose=False, delai=300):
    corps = {"model": modele, "messages": messages, "stream": False,
             "options": {"temperature": 0, "seed": GRAINE, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}}
    if json_impose:
        corps["format"] = "json"
    req = urllib.request.Request(OLLAMA, data=json.dumps(corps).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["content"]


def normaliser_article(texte):
    # Accepte « 14 », « Article 14 bis », « art. 14 », « الفصل 14 مكرر », avec ponctuation finale éventuelle.
    m = re.fullmatch(r"\s*(?:(?:article|art\.?|(?:ال)?فصل)\s*)?(\d+)(?:\s*(bis|ter|quater|مكرر))?\s*[.,;:،؛)\]]*\s*",
                     str(texte), re.IGNORECASE)
    if not m:
        return None
    suffixe = {"مكرر": "bis"}.get(m.group(2), (m.group(2) or "").lower())
    return f"{m.group(1)} {suffixe}".strip()


def articles_dans_texte(texte):
    trouves = []
    for m in list(MOTIF_ARTICLE.finditer(texte)) + list(MOTIF_ARTICLE_AR.finditer(texte)):
        suffixe = {"مكرر": "bis"}.get(m.group(2), (m.group(2) or "").lower())
        lab = f"{m.group(1)} {suffixe}".strip()
        if lab not in trouves:
            trouves.append(lab)
    return trouves


def analyser(variante, brut):
    """Transforme la sortie brute en {reponse, articles_cites, extrait, abstention, json_valide}."""
    if variante in ("P0", "P1"):
        return {"reponse": brut.strip(), "articles_cites": articles_dans_texte(brut), "extrait": "",
                "abstention": False, "json_valide": None}
    try:
        d = json.loads(brut)
        cites = d.get("articles_cites") or []
        if not isinstance(cites, list):
            cites = [cites]
        cites = [c for c in (normaliser_article(x) for x in cites) if c]
        return {"reponse": str(d.get("reponse", "")), "articles_cites": cites,
                "extrait": str(d.get("extrait", "")), "abstention": bool(d.get("abstention", False)),
                "json_valide": True}
    except (json.JSONDecodeError, AttributeError):
        return {"reponse": brut.strip(), "articles_cites": articles_dans_texte(brut), "extrait": "",
                "abstention": False, "json_valide": False}


def verifier_citations(sortie, passages):
    """Garde-fou : si une citation n'est pas un article fourni, ou s'il n'y a aucune citation, abstention."""
    fournis = {p["article"] for p in passages}
    if sortie["abstention"]:
        return {**sortie, "rejet": None}
    if not sortie["articles_cites"]:
        return {**sortie, "abstention": True, "rejet": "aucune_citation", "reponse": MESSAGE_ABSTENTION}
    hors = [a for a in sortie["articles_cites"] if a not in fournis]
    if hors:
        return {**sortie, "abstention": True, "rejet": "citation_non_fournie:" + ",".join(hors),
                "reponse": MESSAGE_ABSTENTION}
    return {**sortie, "rejet": None}


def repondre_rag(question, corpus, variante="P2V", modele=MODELE_DEFAUT, exemples=(), index=None):
    """index (IndexDense) fourni : passages de la recherche hybride ; sinon BM25 top 3 (mode Silver)."""
    if variante == "P0":
        passages = []
    elif index is not None:
        passages = passages_hybrides(question, corpus, index)
    else:
        passages = passages_bm25(question, corpus)
    try:
        brut = appeler_llm(construire_messages(variante, question, passages, exemples), modele,
                           json_impose=variante in ("P2", "P2V", "P3"))
    except OSError as e:  # délai dépassé ou serveur absent : compté comme erreur, jamais comme réponse
        return {"variante": variante, "modele": modele, "passages": [p["article"] for p in passages],
                "brut": "", "reponse": MESSAGE_ABSTENTION, "articles_cites": [], "extrait": "",
                "abstention": True, "json_valide": None, "erreur": type(e).__name__}
    sortie = analyser(variante, brut)
    if variante == "P2V":
        sortie = verifier_citations(sortie, passages)
        if sortie.get("rejet") and sortie["reponse"] == MESSAGE_ABSTENTION:
            sortie["reponse"] = message_abstention(question)
    return {"variante": variante, "modele": modele, "passages": [p["article"] for p in passages],
            "brut": brut, **sortie}


def main():
    import repondre
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="+")
    p.add_argument("--variante", default="P2V", choices=[v for v in VARIANTES if v != "P3"])
    p.add_argument("--modele", default=MODELE_DEFAUT)
    a = p.parse_args()
    r = repondre_rag(" ".join(a.question), repondre.charger(), a.variante, a.modele)
    print(json.dumps({k: r[k] for k in ("variante", "passages", "articles_cites", "abstention", "reponse",
                                        "extrait") if k in r}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
