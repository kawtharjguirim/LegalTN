"""Adaptateur HTTP local ajouté à la reprise, autour de la démo BM25 récupérée.

Lancer : python -X utf8 api.py --port 8000
GET /health ; POST /repondre avec {"question": "...", "k": 3, "mode": "bm25" | "rag"}.
Le mode "rag" (Silver) interroge un LLM local via Ollama ; repli automatique sur BM25 s'il est absent.
Ne lance aucune évaluation et ne modifie ni seuil ni fichiers.
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import sys

from src.demo import repondre
from src.pipeline import traitement

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from rag import rag  # noqa: E402  (bibliothèque standard seulement : l'API reste sans dépendance)


MAX_OCTETS = 16384
MAX_CARACTERES = 2000
STATIC = (Path(__file__).resolve().parent / "static").resolve()
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml", ".webp": "image/webp", ".ico": "image/x-icon",
}


# "bm25" = pipeline de traitement des questions (mode historique, par défaut) ; "rag" = Silver.
MODES = ("bm25", "rag")
_CORPUS_RAG = {}


def corpus_rag():
    """Corpus BM25 utilisé par le RAG (celui des mesures Silver), chargé au premier appel seulement."""
    if not _CORPUS_RAG:
        _CORPUS_RAG.update(repondre.charger())
    return _CORPUS_RAG


def repondre_rag(question, chaine, k):
    """Mode RAG (variante P2V) : LLM local limité aux articles retrouvés, citations vérifiées.

    Si le LLM est injoignable, on répond avec le pipeline et on le signale : la démo ne plante pas."""
    corpus = corpus_rag()
    langue = repondre.detecter_langue(question)
    r = rag.repondre_rag(question, corpus, "P2V")
    if r.get("erreur"):
        repli = chaine.repondre(question, k=k)
        repli.update({"mode": "bm25", "avertissement":
                      "LLM local indisponible : réponse par la recherche classique seule."})
        return repli
    textes = {}
    for lg in ("fr", "ar"):
        for a in corpus[lg].articles:
            if a["article"] in r["articles_cites"]:
                textes.setdefault(a["article"], {"article": a["article"], "page": a["page"]})
                textes[a["article"]].setdefault("texte_" + lg, a["texte"])
    return {
        "mode": "rag", "modele": r["modele"], "langue": langue, "abstention": r["abstention"],
        "reponse": r["reponse"], "extrait": r["extrait"],
        "articles_cites": [textes[a] for a in r["articles_cites"] if a in textes],
        "passages_fournis": r["passages"], "rejet": r.get("rejet"), "candidats": [],
    }


def creer_serveur(port=8000):
    chaine = traitement.pipeline()

    class Requetes(BaseHTTPRequestHandler):
        def envoyer(self, statut, contenu):
            corps = json.dumps(contenu, ensure_ascii=False).encode("utf-8")
            self.send_response(statut)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)

        def servir_fichier(self, chemin):
            """Sert static/index.html sur / et les assets sous /static/.

            Refuse tout chemin sortant du dossier static."""
            if chemin == "/":
                fichier = STATIC / "index.html"
            elif chemin.startswith("/static/"):
                fichier = (STATIC / chemin[len("/static/"):]).resolve()
                if not fichier.is_relative_to(STATIC):
                    self.envoyer(404, {"erreur": "Route inconnue."})
                    return
            else:
                self.envoyer(404, {"erreur": "Route inconnue."})
                return
            if not fichier.is_file() or fichier.suffix not in MIME:
                self.envoyer(404, {"erreur": "Route inconnue."})
                return
            corps = fichier.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", MIME[fichier.suffix])
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)

        def do_GET(self):
            chemin = urlsplit(self.path).path
            if chemin != "/health":
                self.servir_fichier(chemin)
                return
            self.envoyer(200, {
                "statut": "ok",
                "articles_indexes": {langue: len(i["articles"]) for langue, i in chaine.index.items()},
            })

        def rejeter(self, statut, message):
            """Refus avant lecture du corps : on lit (et jette) le corps annoncé, dans une
            limite raisonnable, puis on ferme. Sinon, sous Windows, fermer une connexion qui
            contient encore des octets non lus provoque une réinitialisation TCP : le client
            reçoit ConnectionResetError/AbortedError au lieu du code d'erreur."""
            try:
                taille = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                taille = 0
            if 0 < taille <= 64 * MAX_OCTETS:
                self.rfile.read(taille)
            self.close_connection = True
            self.envoyer(statut, {"erreur": message})

        def do_POST(self):
            if urlsplit(self.path).path != "/repondre":
                self.rejeter(404, "Route inconnue.")
                return
            if self.headers.get_content_type() != "application/json":
                self.rejeter(415, "Envoyer un corps JSON.")
                return
            longueurs = self.headers.get_all("Content-Length", [])
            if len(longueurs) != 1 or self.headers.get("Transfer-Encoding"):
                self.rejeter(400, "Une longueur de requête explicite est nécessaire.")
                return
            try:
                taille = int(longueurs[0])
            except ValueError:
                taille = -1
            if taille < 0:
                self.rejeter(400, "Longueur de requête invalide.")
                return
            if taille > MAX_OCTETS:
                self.rejeter(413, "Requête trop longue.")
                return
            try:
                contenu = json.loads(self.rfile.read(taille).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                self.envoyer(400, {"erreur": "JSON UTF-8 invalide."})
                return
            if not isinstance(contenu, dict):
                self.envoyer(400, {"erreur": "Le corps doit être un objet JSON."})
                return
            question, k = contenu.get("question"), contenu.get("k", 3)
            if not isinstance(question, str) or not question.strip():
                self.envoyer(400, {"erreur": "Fournir une question non vide."})
                return
            if len(question) > MAX_CARACTERES:
                self.envoyer(400, {"erreur": f"Question limitée à {MAX_CARACTERES} caractères."})
                return
            if type(k) is not int or not 1 <= k <= 5:
                self.envoyer(400, {"erreur": "k doit être un entier entre 1 et 5."})
                return
            mode = contenu.get("mode", "bm25")
            if mode not in MODES:
                self.envoyer(400, {"erreur": f"mode doit être l'un de : {', '.join(MODES)}."})
                return
            debut = time.perf_counter()
            if mode == "rag":
                resultat = repondre_rag(question.strip(), chaine, k)
            else:
                resultat = chaine.repondre(question.strip(), k=k)
                resultat["mode"] = "bm25"
            resultat["latence_ms"] = round((time.perf_counter() - debut) * 1000, 3)
            if resultat["abstention"]:
                resultat["message"] = repondre.MESSAGE_ABSTENTION
            self.envoyer(200, resultat)

    return ThreadingHTTPServer(("127.0.0.1", port), Requetes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serveur = creer_serveur(args.port)
    print(f"API LegalTN : http://127.0.0.1:{serveur.server_port}/health", flush=True)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        serveur.server_close()


if __name__ == "__main__":
    main()
