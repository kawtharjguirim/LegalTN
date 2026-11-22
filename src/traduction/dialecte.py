"""Traduction du dialecte tunisien (lettres arabes ou arabizi) vers l'arabe standard, avant la recherche.

Pourquoi : la recherche compare des mots ; le tunisien n'utilise pas le vocabulaire du Code et
l'arabizi était pris pour du français (mesure Gold du 22/11/2026 dans experiments.md).
- Questions en français : jamais envoyées (aucun appel).
- Questions en écriture arabe ou détectées comme arabizi : envoyées à Gemini, qui réécrit le dialecte en
  arabe standard et renvoie l'arabe standard tel quel.
- Cache disque (reproductibilité, quota) ; en cas d'erreur ou sans clé : repli sur la question d'origine.
Seule la question est envoyée à l'API, jamais d'autre donnée.
"""
import json
import os
import re
import threading
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = RACINE / "reports" / "gold" / "traduction_cache.json"
MODELE = "gemini-3.1-flash-lite"
CONSIGNE = ("Tu reçois une question d'un usager sur le Code du travail tunisien. Si elle est écrite en dialecte "
            "tunisien (en lettres arabes ou latines/arabizi), réécris-la en arabe standard moderne clair, sans "
            "répondre et sans ajouter d'information. Si elle est déjà en arabe standard, renvoie-la telle quelle. "
            "Donne uniquement la question.")
ARABE = re.compile(r"[؀-ۿ]")
ARABIZI_CHIFFRE = re.compile(r"(?i)\b[a-z]*[a-z][2-9][a-z]*\b|\b[379][a-z]+\b")
ARABIZI_MOTS = re.compile(r"(?i)\b(chhal|chnowa|chnoua|chkoun|9addech|kadech|nejem|najem|ynajem|3andi|ken|mta3|"
                          r"fel|bech|lezem|barcha|kifech|wela|mte3i|chehriya|khedma|nekhdem|tardouni|nekhou|bla|ytaredni|ynajmou)\b")
_verrou = threading.Lock()


def est_candidat(question):
    """Vrai si la question peut être du dialecte : écriture arabe, ou arabizi (chiffres-lettres, mots typiques)."""
    q = str(question)
    if ARABE.search(q):
        return True
    return bool(ARABIZI_CHIFFRE.search(q)) or len(ARABIZI_MOTS.findall(q)) >= 2


def _cle_api():
    if not os.environ.get("GEMINI_API_KEY"):
        env = RACINE / ".env"
        if env.exists():
            for ligne in env.read_text(encoding="utf-8-sig").splitlines():
                if ligne.strip().startswith("GEMINI_API_KEY="):
                    os.environ["GEMINI_API_KEY"] = ligne.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GEMINI_API_KEY")


def _charger_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _appeler(question, cle, delai=30):
    corps = {"systemInstruction": {"parts": [{"text": CONSIGNE}]},
             "contents": [{"role": "user", "parts": [{"text": question}]}],
             "generationConfig": {"temperature": 0}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODELE}:generateContent",
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": cle})
    with urllib.request.urlopen(req, timeout=delai) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()


def traduire(question, appeler=_appeler):
    """Renvoie {question, origine, traduite, source, erreur}. Ne lève jamais d'exception."""
    q = str(question).strip()
    res = {"question": q, "origine": q, "traduite": False, "source": "aucune", "erreur": None}
    if not est_candidat(q):
        return res
    with _verrou:
        cache = _charger_cache()
    if q in cache:
        t = cache[q]
        return {**res, "question": t, "traduite": t != q, "source": "cache"}
    cle = _cle_api()
    if not cle:
        return {**res, "source": "repli", "erreur": "GEMINI_API_KEY absente"}
    try:
        t = appeler(q, cle)
    except (OSError, KeyError, IndexError, json.JSONDecodeError) as e:
        return {**res, "source": "repli", "erreur": type(e).__name__}
    if not t or not ARABE.search(t):  # sortie vide ou non arabe : on garde la question d'origine
        return {**res, "source": "repli", "erreur": "sortie_non_arabe"}
    with _verrou:
        cache = _charger_cache()
        cache[q] = t
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return {**res, "question": t, "traduite": t != q, "source": MODELE}
