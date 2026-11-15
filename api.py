"""Adaptateur HTTP local ajouté à la reprise, autour de la démo BM25 récupérée.

Lancer : python -X utf8 api.py --port 8000 [--moteur bm25|hybride]
GET /health ; POST /repondre avec {"question": "...", "k": 3}.
- ``bm25`` (défaut) : démo Bronze, bibliothèque standard seule.
- ``hybride`` : moteur Silver (BM25 + e5, abstention par langue, citation bilingue) ;
  nécessite l'environnement Silver (torch, sentence-transformers, modèle e5 en cache).
Ne lance aucune évaluation et ne modifie ni seuil ni fichiers.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from src.demo import repondre


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


NOMS_LANGUE = {"fr": "français", "ar": "arabe"}


class MoteurBM25:
    """Démo Bronze inchangée (BM25 + seuil 9,085), avec étapes visibles."""
    nom = "bm25"

    def __init__(self):
        self.corpus = repondre.charger()

    def articles_indexes(self):
        return {langue: len(c.articles) for langue, c in self.corpus.items()}

    def repondre(self, question, k=3):
        langue = repondre.detecter_langue(question)
        resultat = self.corpus[langue].repondre(question, k=k)
        resultat["moteur"] = self.nom
        resultat["etapes"] = [
            f"Langue détectée : {NOMS_LANGUE[langue]}",
            f"BM25 (seuil {repondre.SEUIL_SCORE_MIN})",
            "Abstention : question hors du Code du travail" if resultat["abstention"]
            else f"Citation : article {resultat['candidats'][0]['article']}",
        ]
        return resultat


def creer_moteur(nom):
    if nom == "bm25":
        return MoteurBM25()
    if nom == "hybride":
        from src.rag.service import MoteurHybride  # import tardif : dépendances Silver
        return MoteurHybride()
    raise ValueError(f"moteur inconnu : {nom}")


def creer_serveur(port=8000, moteur="bm25"):
    moteur = creer_moteur(moteur) if isinstance(moteur, str) else moteur
    verrou = threading.Lock()

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
            llm = getattr(moteur, "llm_disponible", None)
            self.envoyer(200, {
                "statut": "ok",
                "moteur": moteur.nom,
                "llm": bool(llm and llm()),
                "articles_indexes": moteur.articles_indexes(),
            })

        def do_POST(self):
            route = urlsplit(self.path).path
            if route not in {"/repondre", "/resumer"} or (
                    route == "/resumer" and not hasattr(moteur, "resumer")):
                self.envoyer(404, {"erreur": "Route inconnue."})
                return
            if self.headers.get_content_type() != "application/json":
                self.envoyer(415, {"erreur": "Envoyer un corps JSON."})
                return
            longueurs = self.headers.get_all("Content-Length", [])
            if len(longueurs) != 1 or self.headers.get("Transfer-Encoding"):
                self.envoyer(400, {"erreur": "Une longueur de requête explicite est nécessaire."})
                return
            try:
                taille = int(longueurs[0])
            except ValueError:
                taille = -1
            if taille < 0:
                self.envoyer(400, {"erreur": "Longueur de requête invalide."})
                return
            if taille > MAX_OCTETS:
                self.envoyer(413, {"erreur": "Requête trop longue."})
                return
            try:
                contenu = json.loads(self.rfile.read(taille).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                self.envoyer(400, {"erreur": "JSON UTF-8 invalide."})
                return
            if not isinstance(contenu, dict):
                self.envoyer(400, {"erreur": "Le corps doit être un objet JSON."})
                return
            if route == "/resumer":
                self.traiter_resume(contenu)
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
            debut = time.perf_counter()
            with verrou:  # un seul encodage à la fois sur le GPU
                resultat = moteur.repondre(question.strip(), k=k)
            resultat["latence_ms"] = round((time.perf_counter() - debut) * 1000, 3)
            if resultat["abstention"]:
                resultat["message"] = repondre.MESSAGE_ABSTENTION
            self.envoyer(200, resultat)

        def traiter_resume(self, contenu):
            """POST /resumer {"article": "14 bis", "langue": "fr"} : résumé en langage clair."""
            article, langue = contenu.get("article"), contenu.get("langue", "fr")
            if not isinstance(article, str) or not article.strip() or len(article) > 20:
                self.envoyer(400, {"erreur": "Fournir un intitulé d'article (ex. « 14 bis »)."})
                return
            if langue not in {"fr", "ar"}:
                self.envoyer(400, {"erreur": "langue doit valoir fr ou ar."})
                return
            try:
                with verrou:
                    resume = moteur.resumer(article.strip(), langue)
            except KeyError:
                self.envoyer(404, {"erreur": "Article inconnu."})
                return
            except RuntimeError as e:
                self.envoyer(503, {"erreur": str(e)})
                return
            except Exception as e:  # erreur du serveur Ollama
                self.envoyer(502, {"erreur": f"Échec du LLM : {type(e).__name__}."})
                return
            self.envoyer(200, resume)

    return ThreadingHTTPServer(("127.0.0.1", port), Requetes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--moteur", choices=["bm25", "hybride"], default="bm25")
    args = parser.parse_args()
    serveur = creer_serveur(args.port, args.moteur)
    print(f"API LegalTN ({args.moteur}) : http://127.0.0.1:{serveur.server_port}/", flush=True)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        serveur.server_close()


if __name__ == "__main__":
    main()
