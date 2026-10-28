"""Régressions des règles originales v5 ; aucun gold ni fichier n'est produit.

Les petits tableaux ci-dessous sont des fixtures synthétiques de tests logiciels,
pas des annotations du corpus juridique. Les cellules de calcul 2 à 4 sont
exécutées en mémoire. L'export v6 est testé uniquement en répertoire temporaire ;
la cellule de chargement n'est jamais exécutée intégralement.

Lancer : python -m unittest discover -s tests -p test_alignement_notebook.py -v
"""

import ast
import contextlib
import io
import json
import re
import random
import tempfile
import unittest
from pathlib import Path

import pandas as pd


RACINE = Path(__file__).resolve().parents[1]
NOTEBOOK = RACINE / "notebooks/03_alignement_fr_ar_v5.ipynb"


class TestAlignementNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cellules = json.loads(NOTEBOOK.read_bytes())["cells"]

    def aligner(self, articles_ar, articles_fr, verifier=True):
        espace = {
            "re": re, "pd": pd,
            "ar": pd.DataFrame(articles_ar, columns=[
                "article_id", "page", "abroge", "texte_ar", "note_amendement",
            ]),
            "fr": pd.DataFrame(articles_fr, columns=["article_id", "page", "texte_fr"]),
        }
        with contextlib.redirect_stdout(io.StringIO()):
            for numero in (2, 3, 4) if verifier else (2, 3):
                source = "".join(self.cellules[numero]["source"])
                exec(compile(source, f"{NOTEBOOK}:cellule{numero}", "exec"), espace)
        return espace

    def test_suffixes_ar_fr_sont_equivalents(self):
        arabes = [
            ["AR-14-ثالثا", "1", "False", "", ""],
            ["AR-14-خامسا", "1", "False", "", ""],
            ["AR-21-9", "1", "False", "", ""],
            ["AR-385-مكرر", "1", "False", "", ""],
        ]
        francais = [
            ["FR-14", "2", "Article 14 ter. Texte de test."],
            ["FR-14", "2", "Article 14 quinter. Texte de test."],
            ["FR-21", "2", "Article 21 - 9. Texte de test."],
            ["FR-385", "2", "Article 385 — bis. Texte de test."],
        ]
        resultat = self.aligner(arabes, francais)["alignement"]
        self.assertEqual(resultat["statut"].tolist(), ["apparié"] * 4)
        self.assertEqual(resultat["fr_ligne"].tolist(), [0, 1, 2, 3])
        self.assertEqual(resultat["cle"].tolist(), ["14 ter", "14 quinquies", "21-9", "385 bis"])

    def test_article_premier_exclut_la_promulgation(self):
        resultat = self.aligner(
            [["AR-1", "9", "False", "", ""]],
            [["FR-1", "289", "Article premier.- Promulgation."],
             ["FR-1", "285", "Article premier.- Code."]],
        )["alignement"]
        paire = resultat[resultat["article_ar"] == "AR-1"].iloc[0]
        self.assertEqual(paire["page_fr"], "285")
        self.assertEqual(paire["fr_ligne"], 1)
        self.assertIn("hors Code (loi n° 66-27)", resultat["statut"].tolist())

    def test_deux_candidats_fr_ne_sont_pas_tranches_arbitrairement(self):
        resultat = self.aligner(
            [["AR-2", "9", "False", "", ""]],
            [["FR-2", "200", "Article 2.- Première version."],
             ["FR-2", "201", "Article 2.- Autre version."]],
        )["alignement"]
        paire = resultat[resultat["article_ar"] == "AR-2"].iloc[0]
        self.assertEqual(paire["statut"], "doublon à trancher")
        self.assertEqual(paire["fr_ligne"], "")
        self.assertFalse((resultat["statut"] == "apparié").any())

    def test_absence_distincte_de_la_plage_abrogee(self):
        resultat = self.aligner(
            [["AR-2", "9", "False", "", ""], ["AR-272", "90", "True", "", ""]],
            [["FR-1", "285", "Article premier.- Code."]],
        )["alignement"].set_index("article_ar")
        self.assertEqual(resultat.loc["AR-2", "statut"], "absent du français")
        self.assertEqual(resultat.loc["AR-272", "statut"], "abrogé (plage)")

    def test_annees_differentes_signalent_sans_annuler_la_paire(self):
        resultat = self.aligner(
            [["AR-2", "9", "False", "1994", ""]],
            [["FR-2", "285", "Article 2.- Version 1996."]],
        )["alignement"]
        self.assertEqual(resultat.iloc[0]["statut"], "apparié")
        self.assertIn("1994", resultat.iloc[0]["controle"])
        self.assertIn("1996", resultat.iloc[0]["controle"])

    def test_meme_entree_fr_reutilisee_est_rejetee(self):
        with self.assertRaisesRegex(AssertionError, "entrée française appariée deux fois"):
            self.aligner(
                [["AR-97", "9", "False", "", ""], ["AR-97-", "10", "False", "", ""]],
                [["FR-97", "200", "Article 97.- Texte de test."]],
            )

    def test_renvoi_dans_le_corps_ne_devient_pas_une_tete(self):
        resultat = self.aligner(
            [["AR-2", "9", "False", "", ""]],
            [["FR-2", "200", "Voir Article 2 pour les conditions."]],
        )["alignement"]
        self.assertFalse((resultat["statut"] == "apparié").any())

    def test_v6_conserve_les_cellules_de_calcul_v5(self):
        v6 = json.loads((NOTEBOOK.parent / "03_alignement_fr_ar_v6.ipynb").read_bytes())
        for numero in (2, 3, 4):
            with self.subTest(cellule=numero):
                self.assertEqual(v6["cells"][numero]["source"], self.cellules[numero]["source"])

    def test_v6_trouve_la_racine_sans_donnees_brutes(self):
        v6 = json.loads((NOTEBOOK.parent / "03_alignement_fr_ar_v6.ipynb").read_bytes())
        arbre = ast.parse("".join(v6["cells"][1]["source"]))
        fonction = next(n for n in arbre.body if isinstance(n, ast.FunctionDef) and n.name == "trouver_racine")
        espace = {"Path": Path}
        exec(compile(ast.Module(body=[fonction], type_ignores=[]), "<racine v6>", "exec"), espace)
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            (racine / "data/processed").mkdir(parents=True)
            (racine / "notebooks").mkdir()
            self.assertEqual(espace["trouver_racine"](racine / "notebooks"), racine.resolve())

    def test_v6_exports_existants_preserves_et_reexecution_refusee(self):
        v6 = json.loads((NOTEBOOK.parent / "03_alignement_fr_ar_v6.ipynb").read_bytes())
        export = compile("".join(v6["cells"][5]["source"]), "<export v6>", "exec")
        noms = ("alignement_fr_ar_v6.csv", "alignement_echantillon_image_v6.csv", "alignement_resume_v6.json")
        espace = self.aligner(
            [["AR-2", "9", "False", "", ""]],
            [["FR-2", "200", "Article 2.- Texte synthétique de test."]],
        )
        espace.update(random=random, json=json)
        for nom in noms:
            with self.subTest(existant=nom), tempfile.TemporaryDirectory() as dossier:
                sortie = Path(dossier)
                (sortie / nom).write_bytes(b"contenu a conserver")
                espace["OUT_DIR"] = sortie
                with self.assertRaises(FileExistsError):
                    exec(export, espace)
                self.assertEqual((sortie / nom).read_bytes(), b"contenu a conserver")
                self.assertEqual([p.name for p in sortie.iterdir()], [nom])
        with tempfile.TemporaryDirectory() as dossier, contextlib.redirect_stdout(io.StringIO()):
            sortie = Path(dossier)
            espace["OUT_DIR"] = sortie
            exec(export, espace)
            avant = {n: (sortie / n).read_bytes() for n in noms}
            self.assertEqual(json.loads(avant["alignement_resume_v6.json"])["lot_A_appariements_uniques"], 1)
            with self.assertRaises(FileExistsError):
                exec(export, espace)
            self.assertEqual(avant, {n: (sortie / n).read_bytes() for n in noms})


if __name__ == "__main__":
    unittest.main()
