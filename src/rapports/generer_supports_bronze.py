"""Génération des supports de présentation Bronze.

- ``reports/bronze/slides_bronze.pdf`` : 8 diapositives 16:9 (matplotlib,
  polices incorporées par défaut).
- ``reports/bronze/video_secours.gif`` : animation des diapositives en GIF
  (Pillow). ffmpeg étant indisponible, le GIF tient lieu de vidéo de
  secours ; le script de narration est dans ``video_secours_script.md``.

Chaque diapositive distingue les résultats mesurés des validations en
attente ; aucun chiffre n'est inventé.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "reports" / "bronze"

DIAPOS = [
    ("LegalTN — Revue Bronze",
     ["Code du travail tunisien bilingue AR/FR (291 pages).",
      "Composants : alignement AR/FR, obligations par règles,",
      "NER par CRF, retrieval BM25 + extrait cité.",
      "Démo : CLI repondre.py + API HTTP locale /repondre.",
      "", "Ce support distingue mesures réelles et validations en attente."]),
    ("Données et gel",
     ["515 entrées AR, 498 FR (corrigé : 34 corrections).",
      "Dev : 160 paires alignement, 56 questions, 200 candidats.",
      "Test gelé : 40 questions + 30 OCR + 100 candidats obligations,",
      "empreintes SHA-256 vérifiées par la suite de tests.",
      "Annotations : un seul annotateur -> kappa non calculable."]),
    ("Alignement AR/FR",
     ["Règles par numérotation + suffixes (bis/ter/quater...).",
      "Mesuré : 494 appariements, 21 plages abrogées, 4 hors Code,",
      "0 doublon, 6 contrôles d'années à relire.",
      "Reproductible : deux exécutions -> fichiers identiques.",
      "En attente : P/R/F1 sur le lot rappel à annoter (60 AR)."]),
    ("Retrieval BM25 (dev)",
     ["Dev v2 : R@1 = 21/27, R@5 = 23/27 sans seuil.",
      "Seuil historique 9,085 : 27/29 hors périmètre refusés,",
      "4 fausses abstentions (dont le sigle CDI, xfail documenté).",
      "Par langue : FR 0,95 R@5 ; tunisien 0,50 ; AR hors périmètre 3/3.",
      "Mesure sur test gelé : protocole conservé, non relancée."]),
    ("Obligations par règles",
     ["Extracteur : modaux + rôles + conditions (guide v1).",
      "178/200 candidats dev classés obligations.",
      "Évaluateur prêt : refuse tout calcul sans gold annoté.",
      "Lots préparés : 100 candidates test gelé + 200 dev,",
      "champs vides — annotation humaine reste à faire."]),
    ("NER par CRF et reproduction publiée",
     ["CRF (traits ortho + contexte ±2) sur CoNLL-2002 espagnol :",
      "F1 span = 78,90 (référence : Florian 79,05 en 2002).",
      "Baseline publiée reproduite : 35,95 vs 35,86 (+0,09)",
      "via classe majoritaire + appariement le plus long.",
      "Guide NER légal prêt ; gold corpus à annoter."]),
    ("Analyse d'erreurs (dev)",
     ["43 lignes d'erreurs dev catégorisées (2 variantes).",
      "Catégories : hors périmètre accepté, absent du top5,",
      "abstention à tort, article voisin classé devant.",
      "Alignement : 69 étiquettes sans suffixe, 6 années divergentes.",
      "Aucune erreur inventée : seules les observations réelles."]),
    ("État et limites",
     ["Suite logicielle : 47 tests + 1 xfail, aucun échec.",
      "En attente d'annotation humaine : obligations (dev+test),",
      "rappel alignement (60), NER légal (60), gold OCR absent.",
      "Pas de dépôt Git dans la copie : tag bronze impossible ici.",
      "Vidéo de secours : GIF + script (ffmpeg indisponible)."]),
]


def dessiner_diapo(ax, titre, lignes):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0.86), 1, 0.14, color="#1a3a5c"))
    ax.text(0.03, 0.925, titre, fontsize=22, color="white",
            weight="bold", va="center")
    y = 0.78
    for ligne in lignes:
        if ligne:
            ax.text(0.05, y, "\u2022 " + ligne, fontsize=14, va="top")
        y -= 0.075


def generer_pdf() -> Path:
    chemin = SORTIE / "slides_bronze.pdf"
    with PdfPages(chemin) as pdf:
        for titre, lignes in DIAPOS:
            fig = plt.figure(figsize=(13.33, 7.5))
            dessiner_diapo(fig.add_axes([0, 0, 1, 1]), titre, lignes)
            pdf.savefig(fig)
            plt.close(fig)
    return chemin


def generer_gif() -> Path:
    chemin = SORTIE / "video_secours.gif"
    images = []
    for titre, lignes in DIAPOS:
        fig = plt.figure(figsize=(10, 5.625))
        dessiner_diapo(fig.add_axes([0, 0, 1, 1]), titre, lignes)
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        images.append(fig.canvas.buffer_rgba())
        plt.close(fig)
    from PIL import Image
    frames = [Image.frombytes("RGBA", (w, h), bytes(buf)).convert("P",
              palette=Image.ADAPTIVE) for buf in images]
    frames[0].save(chemin, save_all=True, append_images=frames[1:],
                   duration=15000, loop=0)
    return chemin


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    pdf = generer_pdf()
    print(f"PDF : {pdf}")
    gif = generer_gif()
    print(f"GIF : {gif}")
