"""Tests HTTP de l'adaptateur ajouté à la reprise, sans aucune mesure sur test gelé."""

import http.client
import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import api


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = api.creer_serveur(port=0)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        cls.thread.join(timeout=5)

    def requete(self, methode, route, corps=None, type_contenu="application/json"):
        connexion = http.client.HTTPConnection("127.0.0.1", self.serveur.server_port, timeout=10)
        try:
            if corps is not None and not isinstance(corps, bytes):
                corps = json.dumps(corps, ensure_ascii=False).encode("utf-8")
            connexion.request(methode, route, body=corps, headers={"Content-Type": type_contenu})
            reponse = connexion.getresponse()
            return reponse.status, json.loads(reponse.read().decode("utf-8"))
        finally:
            connexion.close()

    def test_health_et_route_inconnue(self):
        statut, resultat = self.requete("GET", "/health")
        self.assertEqual(statut, 200)
        self.assertEqual(resultat["statut"], "ok")
        self.assertGreater(resultat["articles_indexes"]["fr"], 0)
        self.assertGreater(resultat["articles_indexes"]["ar"], 0)
        self.assertEqual(self.requete("GET", "/absent")[0], 404)
        self.assertEqual(self.requete("POST", "/absent", {})[0], 404)

    def test_question_fr_avec_citation_et_latence(self):
        statut, resultat = self.requete("POST", "/repondre", {
            "question": "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?",
            "k": 1,
        })
        self.assertEqual(statut, 200)
        self.assertFalse(resultat["abstention"])
        self.assertEqual(len(resultat["candidats"]), 1)
        self.assertEqual(resultat["candidats"][0]["article"], "14 bis")
        self.assertEqual(resultat["candidats"][0]["page"], "279")
        self.assertIn("Article 14 bis", resultat["candidats"][0]["texte"])
        self.assertGreaterEqual(resultat["latence_ms"], 0)

    def test_question_hors_perimetre(self):
        statut, resultat = self.requete("POST", "/repondre", {
            "question": "Quelle est la capitale de la Tunisie ?",
        })
        self.assertEqual(statut, 200)
        self.assertTrue(resultat["abstention"])
        self.assertEqual(resultat["candidats"], [])
        self.assertTrue(resultat["message"])

    def test_question_arabe_transportee_en_utf8(self):
        statut, resultat = self.requete("POST", "/repondre", {
            "question": "ما هي مدة الإعلام بإنهاء عقد الشغل؟",
        })
        self.assertEqual(statut, 200)
        self.assertEqual(resultat["langue"], "ar")
        self.assertIsInstance(resultat["abstention"], bool)

    def test_requetes_invalides(self):
        cas = [
            b"{",
            b"\xff",
            b"[" * 2000 + b"]" * 2000,
            [],
            {},
            {"question": " "},
            {"question": 123},
            {"question": "texte", "k": True},
            {"question": "texte", "k": 0},
            {"question": "texte", "k": 6},
            {"question": "x" * (api.MAX_CARACTERES + 1)},
        ]
        for corps in cas:
            with self.subTest(corps=repr(corps)[:80]):
                self.assertEqual(self.requete("POST", "/repondre", corps)[0], 400)
        self.assertEqual(self.requete("POST", "/repondre", b"{}", "text/plain")[0], 415)
        self.assertEqual(self.requete("POST", "/repondre", b"x" * (api.MAX_OCTETS + 1))[0], 413)


if __name__ == "__main__":
    unittest.main()


class TestModesSilver(unittest.TestCase):
    """Mode RAG : validation du paramètre et repli BM25 quand le LLM est injoignable (sans appel réel)."""

    @classmethod
    def setUpClass(cls):
        cls.serveur = api.creer_serveur(port=0)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        cls.thread.join(timeout=5)

    requete = TestAPI.requete

    def test_mode_inconnu_refuse(self):
        statut, resultat = self.requete("POST", "/repondre", {"question": "préavis", "mode": "magie"})
        self.assertEqual(statut, 400)
        self.assertIn("mode", resultat["erreur"])

    def test_mode_par_defaut_reste_bm25(self):
        statut, resultat = self.requete("POST", "/repondre", {
            "question": "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?"})
        self.assertEqual(statut, 200)
        self.assertEqual(resultat["mode"], "bm25")

    def test_rag_repli_bm25_si_llm_absent(self):
        ancien = api.rag.OLLAMA
        api.rag.OLLAMA = "http://127.0.0.1:9/api/chat"  # port fermé : simule Ollama éteint
        try:
            statut, resultat = self.requete("POST", "/repondre", {
                "question": "Quel est le préavis de rupture du contrat de travail à durée indéterminée ?",
                "mode": "rag"})
        finally:
            api.rag.OLLAMA = ancien
        self.assertEqual(statut, 200)
        self.assertEqual(resultat["mode"], "bm25")
        self.assertIn("avertissement", resultat)
        self.assertEqual(resultat["candidats"][0]["article"], "14 bis")
