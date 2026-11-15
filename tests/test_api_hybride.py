"""Tests HTTP du moteur Silver (hybride BM25 + e5).

Ignorés si l'environnement Silver (torch, sentence-transformers, e5 en cache) manque.
Questions de démonstration ; aucune mesure sur jeu gelé.
"""

import http.client
import json
import os
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import api

os.environ.setdefault("HF_HUB_OFFLINE", "1")
try:
    MOTEUR = api.creer_moteur("hybride")
except Exception as e:  # dépendances ou modèle absents
    MOTEUR, RAISON = None, f"moteur hybride indisponible : {type(e).__name__}"


@unittest.skipIf(MOTEUR is None, "environnement Silver absent")
class TestAPIHybride(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = api.creer_serveur(port=0, moteur=MOTEUR)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        cls.thread.join(timeout=5)

    def poser(self, question, k=3):
        c = http.client.HTTPConnection("127.0.0.1", self.serveur.server_port, timeout=60)
        try:
            corps = json.dumps({"question": question, "k": k}, ensure_ascii=False).encode()
            c.request("POST", "/repondre", body=corps, headers={"Content-Type": "application/json"})
            r = c.getresponse()
            return r.status, json.loads(r.read().decode())
        finally:
            c.close()

    def test_health_indique_le_moteur(self):
        c = http.client.HTTPConnection("127.0.0.1", self.serveur.server_port, timeout=10)
        c.request("GET", "/health")
        d = json.loads(c.getresponse().read().decode())
        c.close()
        self.assertEqual(d["moteur"], "hybride")

    def test_question_fr_citation_bilingue_et_etapes(self):
        statut, d = self.poser("Quelle est la durée maximale du travail effectif par semaine ?")
        self.assertEqual(statut, 200)
        self.assertFalse(d["abstention"])
        self.assertEqual(d["moteur"], "hybride")
        self.assertEqual(d["candidats"][0]["article"], "79")
        autre = d["candidats"][0]["autre_langue"]
        self.assertEqual(autre["langue"], "ar")
        self.assertIn("الفصل 79", autre["texte"])
        self.assertTrue(any("RRF" in e for e in d["etapes"]))

    def test_question_arabe(self):
        statut, d = self.poser("هل يمكن تكوين اتحادات نقابات؟")
        self.assertEqual(statut, 200)
        self.assertEqual(d["langue"], "ar")
        self.assertFalse(d["abstention"])
        self.assertEqual(d["candidats"][0]["autre_langue"]["langue"], "fr")

    def test_hors_perimetre(self):
        statut, d = self.poser("Quelle est la capitale de la Tunisie ?")
        self.assertEqual(statut, 200)
        self.assertTrue(d["abstention"])
        self.assertEqual(d["candidats"], [])
        self.assertIn("message", d)
