"""Capsule vidéo des paliers Gold et Platinum, sous-titrée en français (MP4 1280x720 + fichier .srt).

Prérequis : application lancée en mode hybride sur --url (``.\\demarrer.ps1 -Port 18765 -Moteur hybride``), Ollama +
qwen2.5:3b, résultats présents dans ``reports/`` (LoRA : ``python -m src.domaine.synthese_lora`` ; biais de langue :
``python -m src.audit.biais_langue --pivot``), tableau de bord généré (``python -m src.rapports.tableau_de_bord``),
et ``pip install pillow imageio-ffmpeg playwright``.

Les vues de l'application et du tableau de bord sont capturées en direct ; **les chiffres des tableaux sont lus dans les
fichiers de résultats**, pas saisis à la main. La vidéo dit aussi ce qui n'est pas fait (validation humaine, étude).

Usage : python -X utf8 -m src.rapports.generer_capsule_platinum --sortie reports/platinum/capsule
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generer_capsule_silver import RACINE, Studio, monter, tableau

R = RACINE / "reports"


def lire(chemin: str) -> dict:
    p = R / chemin
    if not p.exists():
        raise SystemExit(f"Résultat manquant : {p} (voir les prérequis en tête de fichier)")
    return json.loads(p.read_text(encoding="utf-8"))


def f(v, n: int = 3) -> str:
    return f"{float(v):.{n}f}".replace(".", ",")


def vue_tableau_de_bord(s: Studio, titre: str, sous_titre: str, duree: float, decalage: int = 70) -> None:
    """Fait défiler le tableau de bord jusqu'au bloc dont le titre contient ``titre`` puis le capture."""
    p = s.page
    bloc = p.locator(".carte", has_text=titre).first
    bloc.scroll_into_view_if_needed()
    p.evaluate(f"window.scrollBy(0, -{decalage})")
    p.wait_for_timeout(350)
    s.cliche(sous_titre, duree)


def tourner(s: Studio) -> None:
    audit = lire("gold/audit/audit_resultats.json")
    calib = lire("platinum/abstention/calibration.json")
    dom = lire("platinum/domaine/resultats.json")["systemes"]
    lora = lire("platinum/domaine/lora_synthese.json")
    biais = lire("platinum/biais_langue/resultats.json")
    tun = lire("gold/tunisien/tunisien_resultats.json")["methodes"]
    tun7 = lire("gold/tunisien/qwen7b/tunisien_resultats.json")["methodes"]["traduction_fr"]["global"]
    juge = lire("gold/juge/accord_qwen2.5_7b.json")["verdict_claude"]
    refs = lire("platinum/references/resume.json")
    obl = lire("platinum/obligations/evaluation_dev_extracteur.json")
    p = s.page

    # 1. Titre et contenu
    s.carte("<div class='carte'><div class='eyebrow'>VALIDATION DES PALIERS GOLD ET PLATINUM</div><h1>LegalTN</h1>"
            "<p class='sous'>Assistant juridique bilingue arabe / français sur le Code du travail tunisien : "
            "réponses citées, ou abstention. Ce qui a été mesuré, et ce qui ne l'est pas encore.</p></div>",
            "LegalTN répond sur le Code du travail tunisien, avec citation ou abstention. Cette vidéo montre aussi ses limites.", 6)
    s.carte("<div class='carte'><h2>Ce qui s'ajoute depuis le Silver</h2><ul>"
            "<li><b>Gold</b> : audit des hallucinations et de l'abstention, questions en tunisien, divergences arabe/français, LLM-juge</li>"
            "<li><b>Platinum</b> : obligations et rôles, références croisées, classification de domaine, abstention calibrée</li>"
            "<li>Texte arabe corrigé sur l'image du PDF, tableau de bord d'évaluation, protocole d'étude d'utilité</li></ul></div>",
            "Le Gold mesure la fiabilité ; le Platinum ajoute les ressources publiables et la calibration.", 7)

    # 2. Application en direct
    p.goto(s.url + "/")
    p.wait_for_selector("#st-fr")
    p.wait_for_timeout(1200)
    s.cliche("L'application tourne en local, sans service payant.", 4)
    p.click("[data-nav='recherche']")
    p.wait_for_timeout(400)
    s.poser("Quelle est la durée maximale du travail effectif par semaine ?")
    s.defiler_vers("#results", 120)
    s.cliche("En français : la réponse cite l'article 79, avec sa page et sa version arabe.", 6)
    p.click(".lang-btn[data-lang='ar']")
    p.wait_for_timeout(300)
    s.poser("ما هي مدة عطلة الولادة؟")
    s.defiler_vers("#results", 120)
    s.cliche("En arabe, sur la maternité : le texte de l'article 64 affiche maintenant 30 jours, corrigé sur l'image du PDF.", 7)
    p.click(".lang-btn[data-lang='fr']")
    p.wait_for_timeout(300)
    s.poser("Quelle est la capitale de la Tunisie ?")
    s.defiler_vers("#results", 120)
    s.cliche("Hors du Code, le système s'abstient plutôt que d'inventer un article.", 5.5)

    # 3. Tableau de bord en direct
    p.goto(s.url + "/tableau-de-bord")
    p.wait_for_timeout(900)
    s.cliche("Le tableau de bord d'évaluation lit les résultats du projet : aucun chiffre n'y est saisi à la main.", 6)
    vue_tableau_de_bord(s, "Validation humaine", "Chaque bloc dit la nature de sa référence. Ici : ce qui a été relu par un humain, à ce jour presque rien.", 7)
    vue_tableau_de_bord(s, "Audit", "Audit de 493 requêtes : aucun article inventé, aucune question hors Code ayant reçu une réponse.", 7)
    vue_tableau_de_bord(s, "Abstention calibrée", "La courbe risque-couverture : plus on répond, plus le risque d'erreur monte.", 7)
    vue_tableau_de_bord(s, "Classification de domaine", "Classification de domaine en 12 classes : embeddings, LoRA et transfert entre langues.", 7)

    # 4. Tableaux de résultats
    h = audit["hallucinations"]
    s.carte(tableau("Audit : hallucinations et abstention",
                    ["Mesure", "Valeur"],
                    [["Réponses du LLM auditées", str(h["reponses_llm"])],
                     ["Article inventé affiché", f(h["article_invente_affiche"], 0)],
                     ["Question hors Code ayant reçu une réponse", f(h["hors_perimetre_avec_reponse"], 0)],
                     ["Citation hors des extraits (avant filtre)", f(h["citation_hors_contexte_brut"])],
                     ["Décision identique sans accents", f(audit["invariance"]["sans_accents"]["decision"])],
                     ["Décision identique, paraphrase", f(audit["invariance"]["paraphrase"]["decision"])]], 1,
                    "La paraphrase reste le point faible : la recherche dépend du vocabulaire de la loi."),
            "Zéro article inventé sur 326 réponses ; mais une paraphrase change la décision une fois sur deux.", 7)
    d, loo, neuf = calib["dev"], calib["dev_leave_one_out"], calib["etude_12_questions_neuves"]
    s.carte(tableau("Abstention calibrée : décision juste (répondre bien, ou s'abstenir)",
                    ["Jeu", "n", "Décision juste", "IC 95 %"],
                    [["Dev, seuils réglés dessus", str(d["n"]), f(d["decision_juste"]), f"{f(d['ic95_decision_juste'][0], 2)} – {f(d['ic95_decision_juste'][1], 2)}"],
                     ["Dev, leave-one-out", str(d["n"]), f(loo["decision_juste"]), f"{f(loo['ic95'][0], 2)} – {f(loo['ic95'][1], 2)}"],
                     ["12 questions neuves", str(neuf["n"]), f(neuf["decision_juste"]), f"{f(neuf['ic95_decision_juste'][0], 2)} – {f(neuf['ic95_decision_juste'][1], 2)}"]], 2,
                    "Douze questions neuves : l'intervalle reste large."),
            "Sur 12 questions neuves : 9 réponses sur 9 avec le bon article, 0 question hors Code répondue, 1 refus à tort.", 7)
    s.carte(tableau("Questions en tunisien : R@5 par méthode",
                    ["Méthode", "R@5"],
                    [["Recherche multilingue directe", f(tun["multilingue"]["global"]["r_at_5"])],
                     ["Traduction en français (qwen2.5:3b)", f(tun["traduction_fr"]["global"]["r_at_5"])],
                     ["Traduction en français (qwen2.5:7b)", f(tun7["r_at_5"])]], 2,
                    "30 questions dans le Code ; questions rédigées par Claude, à valider."),
            "Traduire en français puis chercher bat la recherche multilingue directe : 0,50 contre 0,03.", 6.5)
    jl = lora["systemes"]
    s.carte(tableau(f"Classification de domaine : macro-F1 (12 domaines, {lora['n_graines']} graines pour LoRA)",
                    ["Système", "Français", "Arabe"],
                    [["TF-IDF + régression logistique", f(dom["tfidf_fr"]["macro_f1"], 2), f(dom["tfidf_ar"]["macro_f1"], 2)],
                     ["e5 + régression logistique", f(dom["e5_fr"]["macro_f1"], 2), f(dom["e5_ar"]["macro_f1"], 2)],
                     ["LoRA sur e5", f"{f(jl['lora_fr']['macro_f1'], 2)} ± {f(jl['lora_fr']['macro_f1_ecart_type'], 2)}", f"{f(jl['lora_ar']['macro_f1'], 2)} ± {f(jl['lora_ar']['macro_f1_ecart_type'], 2)}"],
                     ["Transfert FR → AR / AR → FR (LoRA)", f(jl["lora_transfert_ar_vers_fr"]["macro_f1"], 2), f(jl["lora_transfert_fr_vers_ar"]["macro_f1"], 2)]], 2,
                    "Étiquettes tirées de la structure du Code ; transfert : colonne = langue de test."),
            "Sur trois graines, le fine-tuning LoRA gagne 4 à 8 points sur e5 ; le transfert entre langues reste inférieur à l'apprentissage dans la langue.", 8)
    s.carte(tableau("Obligations et références croisées",
                    ["Mesure", "Valeur"],
                    [["Détection d'obligation (F1, dev)", f(obl["detection_obligation"]["f1"], 2)],
                     ["Type : obligation / interdiction (F1)", f"{f(obl['modal_par_classe']['obligation']['f1'], 2)} / {f(obl['modal_par_classe']['interdiction']['f1'], 2)}"],
                     ["Rôle : exactitude des classes / F1 macro", f"{f(obl['role_exactitude_classes'], 2)} / {f(obl['role_macro_f1'], 2)}"],
                     ["Renvois croisés extraits (FR / AR)", f"{refs['fr']['mentions']} / {refs['ar']['mentions']}"],
                     ["Renvois identiques arabe/français", f"{refs['coherence_ar_fr']['identiques']} sur {refs['coherence_ar_fr']['avec_renvoi']}"]], 2,
                    "Obligations : références de Claude non relues. Le contrôle des renvois a servi à trouver des défauts d'OCR."),
            "L'extracteur trouve le type d'obligation, mais le rôle seulement six fois sur dix ; les renvois ont servi à corriger l'arabe.", 7)
    mono, pv = biais["configurations"]["monolingue"], biais.get("pivot_traduction")
    lignes_biais = [["Recherche en français", f(mono["r_at_1_fr"], 2), f(mono["r_at_5_fr"], 2)],
                    ["Recherche en arabe", f(mono["r_at_1_ar"], 2), f(mono["r_at_5_ar"], 2)]]
    if pv:
        lignes_biais.append([f"Arabe, traduit en français ({pv['modele_traduction']})", f(pv["r_at_1_ar"], 2), f(pv["r_at_5_ar"], 2)])
    s.carte(tableau("Biais de langue : même question, deux langues (21 paires)", ["Méthode", "R@1", "R@5"], lignes_biais, 2 if pv else None,
                    "Étendre la recherche à l'autre langue ne corrige pas le biais : le français se dégrade."),
            "Le français retrouve le bon article en tête, l'arabe moins souvent : le biais est mesuré, il n'est pas toujours corrigé.", 7)
    s.carte(tableau("LLM-juge de fidélité (qwen2.5:7b)", ["Mesure", "Valeur"],
                    [["κ de Cohen, 3 classes, contre Claude", f(juge["kappa_3_classes"], 2)],
                     ["Réponses infidèles signalées", "13 sur 13"],
                     ["Fausses alertes (réponses fidèles)", "6 sur 32"],
                     ["Verdicts humains enregistrés", "0 sur 56"]], 3,
                    "La référence est un jugement de Claude : le juge n'est pas encore validé contre un humain."),
            "Le juge signale toutes les réponses infidèles mais il n'est validé que contre Claude, pas contre un humain.", 7)

    # 5. Limites
    s.carte("<div class='carte'><h2>Ce qui reste à faire</h2><ul>"
            "<li><b>Relecture humaine</b> des références de Claude (NER, obligations, divergences, juge)</li>"
            "<li><b>Étude d'utilité</b> avec des étudiants : protocole et outils prêts, aucune passation</li>"
            "<li><b>Publication</b> : licence de l'édition source à clarifier</li>"
            "<li>7 corrections du texte arabe à confirmer sur image</li></ul></div>",
            "Ce qui manque : relectures humaines, étude avec des étudiants, licence et publication.", 8)
    s.carte("<div class='carte'><div class='eyebrow'>LEGALTN · PALIERS GOLD ET PLATINUM</div><h1>Merci</h1>"
            "<p class='sous'>Information juridique générale, pas un conseil juridique.</p></div>", "", 3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18765")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/capsule")
    parser.add_argument("--nom", default="capsule_platinum_legaltn")
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
