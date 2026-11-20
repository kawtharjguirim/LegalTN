"""Capsule vidéo de la démo Silver, sous-titrée en français (MP4 1280x720 + fichier .srt).

Prérequis : application lancée en mode hybride sur --url (``.\\demarrer.ps1 -Port 18765 -Moteur
hybride``), Ollama + qwen2.5:3b, modèles NER de démo dans ``models/ner/``, et
``pip install pillow imageio-ffmpeg playwright`` (Playwright pilote le Chrome installé).

Toutes les vues de l'application sont capturées en direct ; les sorties NER proviennent d'une
exécution réelle de ``src.ner_juridique.predire``. Les chiffres des tableaux sont ceux de
``reports/silver/*/RESULTATS.md``.

Usage : python -X utf8 -m src.rapports.generer_capsule_silver --sortie reports/silver/capsule
"""

from __future__ import annotations

import argparse
import html
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
L, H = 1280, 720
POLICE = "C:/Windows/Fonts/segoeui.ttf"
POLICE_GRAS = "C:/Windows/Fonts/segoeuib.ttf"


@dataclass
class Plan:
    image: Path
    duree: float
    sous_titre: str


# ---------------------------------------------------------------- gabarits HTML
STYLE = """
<style>
 *{box-sizing:border-box;margin:0;padding:0}
 body{width:1280px;height:720px;font-family:"Segoe UI",Arial,sans-serif;background:#F5F3EE;
      color:#344054;display:flex;align-items:center;justify-content:center}
 .carte{width:1120px;background:#fff;border:1px solid #E4E1D8;border-radius:18px;padding:44px 52px;
        box-shadow:0 8px 24px rgba(23,50,77,.10)}
 h1{color:#17324D;font-size:46px;margin-bottom:14px} h2{color:#17324D;font-size:30px;margin-bottom:18px}
 .sous{font-size:24px;color:#667085;line-height:1.5} .eyebrow{color:#C9363B;font-weight:700;
      letter-spacing:.12em;font-size:16px;margin-bottom:16px}
 table{width:100%;border-collapse:collapse;font-size:21px} th,td{padding:11px 14px;text-align:left;
      border-bottom:1px solid #EDEAE2} th{color:#667085;font-weight:600;font-size:17px}
 td.n{text-align:right;font-variant-numeric:tabular-nums} tr.best td{background:#DCE9E2;font-weight:700}
 .note{margin-top:18px;font-size:17px;color:#98A2B3}
 .term{width:1180px;background:#0F1720;border-radius:14px;padding:28px 34px;color:#D0D7DE;
       font-family:Consolas,monospace;font-size:21px;line-height:1.75;box-shadow:0 8px 24px rgba(0,0,0,.3)}
 .term .p{color:#7EE787} .term .c{color:#79C0FF} .term .r{color:#D2A8FF} .term .m{color:#FFA657}
 .ent{background:rgba(121,192,255,.16);border:1px solid rgba(121,192,255,.35);border-radius:6px;
      padding:1px 6px;margin:0 2px;white-space:nowrap}
 .badge{font-family:"Segoe UI",sans-serif;font-size:13px;font-weight:700;color:#0F1720;
      background:#FFA657;border-radius:4px;padding:1px 5px;margin:0 5px;vertical-align:2px}
 .ar{font-family:"Segoe UI",Tahoma,sans-serif;font-size:23px}
 .ligne{display:flex;align-items:baseline;gap:14px;margin:6px 0}
 .nom{flex:0 0 130px} .txt{flex:1} .duree{flex:0 0 auto;color:#6E7681;font-size:16px}
 .term .titre{color:#8B949E;font-size:17px;margin-bottom:4px}
 ul{font-size:24px;line-height:1.9;margin-left:28px}
</style>"""


def page_html(corps: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'>{STYLE}</head><body>{corps}</body></html>"


def tableau(titre: str, entetes: list[str], lignes: list[list[str]], meilleure: int | None,
            note: str = "") -> str:
    th = "".join(f"<th style='text-align:{'right' if j else 'left'}'>{html.escape(e)}</th>"
                 for j, e in enumerate(entetes))
    corps = ""
    for i, l in enumerate(lignes):
        cellules = "".join(f"<td class='{'n' if j else ''}'>{html.escape(c)}</td>" for j, c in enumerate(l))
        corps += f"<tr class='{'best' if i == meilleure else ''}'>{cellules}</tr>"
    return (f"<div class='carte'><h2>{html.escape(titre)}</h2><table><tr>{th}</tr>{corps}</table>"
            f"<p class='note'>{html.escape(note)}</p></div>")


# ---------------------------------------------------------------- sous-titres
def incruster(source: Path, texte: str, cible: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(source).convert("RGB").resize((L, H))
    if texte:
        police = ImageFont.truetype(POLICE, 30)
        lignes = textwrap.wrap(texte, width=68)[:3]
        hauteur_ligne = 42
        haut = H - 34 - hauteur_ligne * len(lignes) - 20
        calque = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(calque)
        largeur = max(d.textlength(l, font=police) for l in lignes)
        x0 = (L - largeur) / 2 - 22
        d.rounded_rectangle([x0, haut, L - x0, H - 30], radius=12, fill=(15, 23, 32, 205))
        for k, l in enumerate(lignes):
            w = d.textlength(l, font=police)
            d.text(((L - w) / 2, haut + 10 + k * hauteur_ligne), l, font=police, fill=(255, 255, 255, 255))
        img = Image.alpha_composite(img.convert("RGBA"), calque).convert("RGB")
    img.save(cible)


def horodatage(s: float) -> str:
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# ---------------------------------------------------------------- capture
class Studio:
    def __init__(self, url: str, dossier: Path):
        from playwright.sync_api import sync_playwright

        self.url, self.dossier = url.rstrip("/"), dossier
        self.pw = sync_playwright().start()
        self.navigateur = self.pw.chromium.launch(channel="chrome", headless=True)
        self.page = self.navigateur.new_page(viewport={"width": L, "height": H}, locale="fr-FR")
        self.carte_page = self.navigateur.new_page(viewport={"width": L, "height": H})
        self.n = 0
        self.plans: list[Plan] = []

    def _fichier(self) -> Path:
        self.n += 1
        return self.dossier / "brut" / f"{self.n:03d}.png"

    def cliche(self, sous_titre: str, duree: float, page=None) -> None:
        f = self._fichier()
        (page or self.page).screenshot(path=str(f))
        self.plans.append(Plan(f, duree, sous_titre))

    def carte(self, corps: str, sous_titre: str, duree: float) -> None:
        self.carte_page.set_content(page_html(corps))
        self.carte_page.wait_for_timeout(150)
        self.cliche(sous_titre, duree, self.carte_page)

    def poser(self, question: str) -> None:
        p = self.page
        p.fill("#input-q", question)
        p.press("#input-q", "Enter")
        p.wait_for_selector("#results .card-answer, #results .abs-card", timeout=120_000)
        p.wait_for_timeout(900)  # fin des animations d'apparition

    def defiler_vers(self, selecteur: str, decalage: int = 90) -> None:
        self.page.eval_on_selector(selecteur, f"""e => {{
            const c = document.querySelector('.content');
            c.scrollTop += e.getBoundingClientRect().top - c.getBoundingClientRect().top - {decalage};
        }}""")
        self.page.wait_for_timeout(250)

    def fermer(self) -> None:
        self.navigateur.close()
        self.pw.stop()


def sortie_ner(phrase: str) -> list[str]:
    """Exécution réelle du NER de démo ; renvoie les lignes « Règles » et modèle."""
    import os

    # Sur processeur : la carte graphique (4 Go) est déjà occupée par e5 et le LLM de la démo.
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "-1", "OPENBLAS_NUM_THREADS": "1"}
    r = subprocess.run([sys.executable, "-X", "utf8", "-B", "-m", "src.ner_juridique.predire", phrase],
                       cwd=RACINE, capture_output=True, text=True, encoding="utf-8", env=env)
    lignes = [l for l in r.stdout.splitlines() if l.startswith(("Règles", "fr_", "ar_"))]
    if len(lignes) >= 2:
        return lignes
    # Repli : sorties réelles enregistrées (même modèle, mêmes phrases), si la machine manque de mémoire.
    import json

    reference = json.loads((RACINE / "reports/silver/capsule/ner_sorties_reference.json").read_text(encoding="utf-8"))
    if phrase not in reference:
        raise RuntimeError(f"Sortie NER inattendue (code {r.returncode}) :\n{r.stdout}\n{r.stderr[-800:]}")
    print(f"  NER en direct impossible (code {r.returncode}) : sorties enregistrées du 16/11 utilisées.")
    return reference[phrase]


def colorer_ner(ligne: str) -> str:
    import re

    nom, _, reste = ligne.partition(":")
    reste = reste.strip()
    duree = ""
    m = re.search(r"\s*\((\d+) ms\)\s*$", reste)
    if m:
        duree, reste = f"<span class='duree'>{m.group(1)} ms</span>", reste[:m.start()]
    reste = html.escape(reste)
    # Chaque entité est isolée (bdi) avec son type en badge : l'ordre reste correct en arabe.
    reste = re.sub(r"\[([^\]]+)\](ROLE|INSTITUTION|DELAI|MONTANT)",
                   r"<bdi class='ent'>\1<span class='badge'>\2</span></bdi>", reste)
    classe = "r" if nom.strip() == "Règles" else "c"
    arabe = any("\u0600" <= c <= "\u06ff" for c in ligne)
    texte = f"<bdi dir='rtl' class='ar'>{reste}</bdi>" if arabe else reste
    return (f"<div class='ligne'><span class='nom {classe}'>{html.escape(nom.strip())}</span>"
            f"<span class='txt' dir='{'rtl' if arabe else 'ltr'}'>{texte}</span>{duree}</div>")


# ---------------------------------------------------------------- scénario
def tourner(s: Studio) -> None:
    p = s.page
    # 1. Titre
    s.carte("<div class='carte'><div class='eyebrow'>VALIDATION DU PALIER SILVER</div>"
            "<h1>LegalTN</h1><p class='sous'>Assistant juridique bilingue arabe / français sur le Code du "
            "travail tunisien : réponses citées, ou abstention.</p></div>",
            "LegalTN répond aux questions sur le Code du travail tunisien, en français et en arabe.", 5)
    s.carte("<div class='carte'><h2>Ce qu'apporte le palier Silver</h2><ul>"
            "<li>Alignement des articles arabe ↔ français par embeddings (LaBSE, e5)</li>"
            "<li>Recherche hybride BM25 + e5 avec abstention calibrée par langue</li>"
            "<li>Réponse rédigée par un LLM local (qwen2.5:3b) avec citation vérifiée</li>"
            "<li>NER fine-tuné : CamemBERT, AraBERT, XLM-R sur 3 graines</li></ul></div>",
            "Au Bronze, la recherche était lexicale. Le Silver ajoute encodeurs, RAG, LLM et NER fine-tuné.", 6)

    # 2. Accueil
    p.goto(s.url + "/")
    p.wait_for_selector("#st-fr")
    p.wait_for_timeout(1500)
    s.cliche("L'application tourne en local : 496 articles français et 491 articles arabes indexés.", 4.5)

    # 3. Question française
    p.click("[data-nav='recherche']")
    p.wait_for_timeout(400)
    s.poser("Quelles sont les attributions des conseils de prud'hommes ?")
    s.defiler_vers("#results", 120)
    s.cliche("Question en français. Le LLM rédige une réponse et cite l'article 183, le bon article.", 6)
    s.cliche("Le moteur BM25 du Bronze citait l'article 182 : la recherche hybride corrige l'erreur.", 5)
    p.click(".steps summary")
    p.wait_for_timeout(300)
    s.defiler_vers(".steps", 40)
    s.cliche("Toutes les étapes sont visibles : langue, BM25, recherche dense e5, fusion RRF, citation.", 6)
    s.cliche("Le serveur vérifie que l'article cité par le LLM fait partie des extraits retrouvés.", 5)
    p.click(".card-answer .other-lang summary")
    p.wait_for_timeout(300)
    s.defiler_vers(".card-answer .other-lang", 160)
    s.cliche("La citation est bilingue : le même article est affiché dans sa version arabe.", 5)

    # 4. Question arabe
    p.click(".lang-btn[data-lang='ar']")
    p.wait_for_timeout(300)
    s.poser("في أي الحالات لا ينطبق تحجير العمل الليلي على النساء؟")
    s.defiler_vers("#results", 120)
    s.cliche("En arabe, la réponse est rédigée en arabe et cite l'article 68. Le BM25 citait l'article 29.", 6)
    s.cliche("Sur le dev, la recherche hybride gagne 10 points de rappel en arabe (0,62 contre 0,52).", 5)

    # 5. Abstentions
    p.click(".lang-btn[data-lang='fr']")
    p.wait_for_timeout(300)
    s.poser("Quelle est la capitale de la Tunisie ?")
    p.click(".steps summary")
    p.wait_for_timeout(300)
    s.defiler_vers("#results", 120)
    s.cliche("Hors du Code du travail, le système s'abstient plutôt que d'inventer un article.", 5.5)
    s.poser("Quel est le délai de préavis pour rompre un CDI ?")
    p.click(".steps summary")
    p.wait_for_timeout(300)
    s.defiler_vers("#results", 120)
    s.cliche("Limite assumée : « CDI » n'apparaît pas dans le Code, d'où une abstention à tort.", 6)

    # 6. NER en direct
    phrases = ["Les stagiaires ne peuvent être employés plus de six heures par jour.",
               "يجب على مدير الشركة التصريح بكل متربص لدى الصندوق في أجل ثمانية أيام."]
    blocs = ""
    for ph in phrases:
        sortie = sortie_ner(ph)
        blocs += (f"<div class='p'>&gt; python -m src.ner_juridique.predire</div>"
                  + "".join(colorer_ner(l) for l in sortie) + "<br>")
    s.carte(f"<div class='term'>{blocs}</div>",
            "NER fine-tuné : XLM-R en français, AraBERT en arabe, comparés aux règles.", 5.5)
    s.carte(f"<div class='term'>{blocs}</div>",
            "Le modèle reconnaît « les stagiaires » et, en arabe, « le directeur de la société » comme "
            "rôles : les règles les ratent.", 6.5)

    # 7. Résultats
    s.carte(tableau("Alignement arabe ↔ français (160 paires vérifiées)",
                    ["Système", "Précision", "Rappel"],
                    [["Numéro d'article seul", "0,894", "0,894"],
                     ["LaBSE, sans en-tête numéroté", "0,975", "0,975"],
                     ["e5, sans en-tête + normalisation arabe", "0,956", "0,956"],
                     ["Hybride embeddings + numéro", "1,000", "1,000"]], 3,
                    "Ablation : la normalisation orthographique arabe dégrade les encodeurs."),
            "Alignement : 97,5 % sans le numéro d'article, 100 % en combinant embeddings et numéro.", 6)
    s.carte(tableau("Recherche — 77 questions de développement",
                    ["Système", "R@1 FR", "R@1 AR", "Fausses abstentions"],
                    [["BM25 (Bronze)", "0,95", "0,52", "7"],
                     ["Hybride e5, seuil global", "1,00", "0,62", "21"],
                     ["Hybride e5, seuil par langue", "1,00", "0,62", "3"]], 2,
                    "Seuils réglés en validation croisée leave-one-out ; aucun jeu de test gelé utilisé."),
            "Un seuil d'abstention unique rejette les questions arabes valides : il faut un seuil par langue.", 6.5)
    s.carte(tableau("LLM qwen2.5:3b — 3 stratégies de prompting",
                    ["Stratégie", "Article cité", "Citation inventée", "Abstention à tort"],
                    [["zero-shot", "0,542", "0,028", "0,250"],
                     ["few-shot", "0,625", "0,023", "0,083"],
                     ["citation forcée", "0,667", "0,000", "0,167"]], 2,
                    "Plafond : la référence n'est dans les 3 extraits que pour 81 % des questions."),
            "La citation forcée supprime les citations inventées, mais augmente les refus injustifiés.", 6.5)
    s.carte(tableau("NER — F1 strict sur 120 phrases de développement (pré-gold)",
                    ["Langue", "Règles", "CRF (Bronze)", "Fine-tuné"],
                    [["Français", "0,423", "0,406", "XLM-R 0,479"],
                     ["Arabe", "0,484", "0,364", "AraBERT 0,416"]], None,
                    "Référence annotée par Claude selon le guide, pas encore relue par un humain."),
            "En français, XLM-R dépasse les règles qui l'ont entraîné ; en arabe, pas encore.", 6.5)
    s.carte(tableau("NER — pourquoi l'accord avec les règles trompait",
                    ["Mesure (XLM-R, français)", "F1"],
                    [["Accord avec les règles (validation silver)", "0,886"],
                     ["Pré-gold, F1 strict (bornes exactes)", "0,479"],
                     ["Pré-gold, F1 souple (chevauchement)", "0,644"]], 1,
                    "Les modèles héritent des oublis des règles : le rappel est leur point faible."),
            "L'accord avec les règles surestimait la qualité : il fallait une référence corrigée.", 6)

    # 8. Conclusion
    s.carte("<div class='carte'><h2>Limites et suite</h2><ul>"
            "<li>Une citation correcte ne garantit pas une réponse fidèle → LLM-juge (Gold)</li>"
            "<li>Le LLM n'est pas déterministe malgré la température 0</li>"
            "<li>Questions en tunisien (arabizi) : 0/6 → translittération (Gold)</li>"
            "<li>NER : relecture humaine du pré-gold, puis silver corrigé pour réentraîner</li></ul></div>",
            "Prochaines étapes : fidélité des réponses, questions en tunisien et relecture humaine du NER.", 7)
    s.carte("<div class='carte'><div class='eyebrow'>LEGALTN · PALIER SILVER</div><h1>Merci</h1>"
            "<p class='sous'>Information juridique générale, pas un conseil juridique.</p></div>", "", 3)


# ---------------------------------------------------------------- montage
def monter(plans: list[Plan], dossier: Path, nom: str) -> tuple[Path, Path]:
    import imageio_ffmpeg

    images = dossier / "images"
    images.mkdir(parents=True, exist_ok=True)
    liste, srt, t = [], [], 0.0
    for i, pl in enumerate(plans, 1):
        cible = images / f"{i:03d}.png"
        incruster(pl.image, pl.sous_titre, cible)
        liste.append(f"file '{cible.resolve().as_posix()}'\nduration {pl.duree}")
        if pl.sous_titre:
            srt.append(f"{len(srt) + 1}\n{horodatage(t)} --> {horodatage(t + pl.duree - 0.05)}\n"
                       f"{textwrap.fill(pl.sous_titre, 60)}\n")
        t += pl.duree
    liste.append(f"file '{(images / f'{len(plans):03d}.png').resolve().as_posix()}'")  # requis par concat
    (dossier / "plans.txt").write_text("\n".join(liste), encoding="utf-8")
    fichier_srt = dossier / f"{nom}.srt"
    fichier_srt.write_text("\n".join(srt), encoding="utf-8-sig")
    video = dossier / f"{nom}.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(dossier / "plans.txt"), "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", str(video)], check=True)
    print(f"Durée : {t:.1f} s ; {len(plans)} plans ; {len(srt)} sous-titres")
    return video, fichier_srt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18765")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/silver/capsule")
    parser.add_argument("--nom", default="capsule_silver_legaltn")
    args = parser.parse_args()
    (args.sortie / "brut").mkdir(parents=True, exist_ok=True)
    studio = Studio(args.url, args.sortie)
    try:
        tourner(studio)
    finally:
        studio.fermer()
    video, srt = monter(studio.plans, args.sortie, args.nom)
    print(f"-> {video}\n-> {srt}")


if __name__ == "__main__":
    main()
