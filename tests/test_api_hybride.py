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
from unittest import mock

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

    # ---------------------------------------------------- LLM simulé (pas d'Ollama)
    def simuler_llm(self, disponible=True, sortie=""):
        from src.rag import generer

        appels = []
        patchs = [mock.patch.object(generer, "disponible", return_value=disponible),
                  mock.patch.object(generer, "appeler",
                                    side_effect=lambda m, *a, **k: appels.append(m) or sortie)]
        for p in patchs:
            p.start()
            self.addCleanup(p.stop)
        MOTEUR._llm_etat = (0.0, False)  # force une nouvelle vérification
        self.addCleanup(setattr, MOTEUR, "_llm_etat", (0.0, False))
        return appels

    def test_llm_citation_valide(self):
        appels = self.simuler_llm(sortie="La durée ne peut excéder 48 heures [Article 79].")
        _, d = self.poser("Quelle est la durée maximale du travail effectif par semaine ?")
        r = d["reponse_redigee"]
        self.assertEqual(r["citations"], ["79"])
        self.assertFalse(r["abstention"])
        self.assertIn("48 heures", r["texte"])
        self.assertIn("citation vérifiée", d["etapes"][-1])
        # Le LLM ne reçoit que les articles retrouvés (3 au plus).
        self.assertEqual(appels[0][-1]["content"].count("[Article "), 3)

    def test_llm_citation_inventee_rejetee(self):
        self.simuler_llm(sortie="La durée est de 40 heures [Article 999].")
        _, d = self.poser("Quelle est la durée maximale du travail effectif par semaine ?")
        r = d["reponse_redigee"]
        self.assertTrue(r["abstention"])
        self.assertNotIn("999", r["texte"])
        self.assertFalse(d["abstention"])  # les extraits restent affichés

    def test_llm_indisponible_extraits_seuls(self):
        self.simuler_llm(disponible=False)
        _, d = self.poser("Quelle est la durée maximale du travail effectif par semaine ?")
        self.assertIsNone(d["reponse_redigee"])
        self.assertIn("indisponible", d["etapes"][-1])
        self.assertTrue(d["candidats"])

    def test_resume(self):
        self.simuler_llm(sortie="Le travail est limité à 48 heures par semaine.")
        statut, d = self.envoyer_json("/resumer", {"article": "79", "langue": "fr"})
        self.assertEqual(statut, 200)
        self.assertIn("48 heures", d["resume"])
        self.assertEqual(self.envoyer_json("/resumer", {"article": "9999", "langue": "fr"})[0], 404)
        self.assertEqual(self.envoyer_json("/resumer", {"article": "79", "langue": "en"})[0], 400)

    def test_resume_sans_llm(self):
        self.simuler_llm(disponible=False)
        self.assertEqual(self.envoyer_json("/resumer", {"article": "79", "langue": "fr"})[0], 503)

    def envoyer_json(self, route, corps):
        c = http.client.HTTPConnection("127.0.0.1", self.serveur.server_port, timeout=60)
        try:
            c.request("POST", route, body=json.dumps(corps).encode(),
                      headers={"Content-Type": "application/json"})
            r = c.getresponse()
            return r.status, json.loads(r.read().decode())
        finally:
            c.close()

    def test_hors_perimetre(self):
        statut, d = self.poser("Quelle est la capitale de la Tunisie ?")
        self.assertEqual(statut, 200)
        self.assertTrue(d["abstention"])
        self.assertEqual(d["candidats"], [])
        self.assertIn("message", d)
