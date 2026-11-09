"""Adaptateur HTTP local ajouté à la reprise, autour de la démo BM25 récupérée.

Lancer : python -X utf8 api.py --port 8000
GET /health ; POST /repondre avec {"question": "...", "k": 3}.
Ne lance aucune évaluation et ne modifie ni seuil ni fichiers.
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from src.demo import repondre
from src.pipeline import traitement


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

        def do_POST(self):
            if urlsplit(self.path).path != "/repondre":
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
            resultat = chaine.repondre(question.strip(), k=k)
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
