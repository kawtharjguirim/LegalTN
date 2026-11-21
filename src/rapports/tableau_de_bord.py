"""Tableau de bord d'évaluation de LegalTN : une page HTML autonome, générée à partir des résultats.

Lit les fichiers de ``reports/`` (JSON, CSV) et les annotations de ``data/`` ; n'invente aucun
chiffre. Chaque bloc indique la **nature de la référence** (humain, Claude non relu, automatique) et
le tableau « Validation humaine » dit ce qui reste à relire. Un résultat absent est signalé, pas masqué.

Sortie : ``static/tableau_de_bord.html`` (servi par l'API sur ``/tableau-de-bord``).

Usage : python -X utf8 -m src.rapports.tableau_de_bord
"""

from __future__ import annotations

import csv
import html
import json
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "static/tableau_de_bord.html"
R = RACINE / "reports"

BADGES = {"humain": ("Référence humaine", "b-h"), "claude": ("Référence Claude, non relue", "b-c"),
          "auto": ("Mesure automatique", "b-a"), "mixte": ("Références mixtes", "b-m")}


# ------------------------------------------------------------------ lecture
def json_(chemin: Path):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def csv_(chemin: Path) -> list[dict]:
    try:
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def f(v, n: int = 3) -> str:
    """Nombre au format français ; « – » si absent."""
    if v is None or v == "":
        return "–"
    try:
        return f"{float(v):.{n}f}".replace(".", ",")
    except (TypeError, ValueError):
        return html.escape(str(v))


def e(t) -> str:
    return html.escape(str(t))


def num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ composants HTML
def badge(nature: str) -> str:
    texte, cls = BADGES[nature]
    return f'<span class="badge {cls}">{texte}</span>'


def carte(titre: str, nature: str, corps: str, note: str = "", large: bool = False) -> str:
    note_html = f'<p class="note">{note}</p>' if note else ""
    return (f'<section class="carte{" large" if large else ""}"><header><h2>{e(titre)}</h2>{badge(nature)}</header>'
            f"{corps}{note_html}</section>")


def absent(commande: str) -> str:
    return f'<p class="absent">Résultat non disponible. Commande : <code>{e(commande)}</code></p>'


def barre(libelle: str, valeur, maxi: float = 1.0, detail: str = "", classe: str = "") -> str:
    v = num(valeur)
    if v is None:
        return f'<div class="ligne"><span class="lib">{e(libelle)}</span><span class="vide">–</span></div>'
    larg = max(0.0, min(100.0, 100.0 * v / maxi))
    return (f'<div class="ligne"><span class="lib">{e(libelle)}</span><span class="piste"><i class="{classe}" style="width:{larg:.1f}%"></i></span>'
            f'<span class="val">{f(v)}</span>{f"<span class=det>{e(detail)}</span>" if detail else ""}</div>')


def tableau(entetes: list[str], lignes: list[list], classes: list[str] | None = None) -> str:
    th = "".join(f"<th>{e(h)}</th>" for h in entetes)
    corps = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in lignes)
    return f'<div class="defile"><table><thead><tr>{th}</tr></thead><tbody>{corps}</tbody></table></div>'


def tuile(valeur: str, libelle: str, etat: str = "") -> str:
    return f'<div class="tuile {etat}"><b>{valeur}</b><span>{e(libelle)}</span></div>'


# ------------------------------------------------------------------ blocs
def bloc_synthese() -> str:
    audit = json_(R / "gold/audit/audit_resultats.json")
    calib = json_(R / "platinum/abstention/calibration.json")
    juge = json_(R / "gold/juge/accord_qwen2.5_7b.json")
    rag = {x["configuration"]: x for x in csv_(R / "silver/rag/ablations_rag.csv")}
    final = rag.get("hybride[multilingual-e5-base]+seuil_par_langue", {})
    t = []
    if audit:
        h = audit["hallucinations"]
        t.append(tuile(f(h["article_invente_affiche"], 0), "article inventé affiché", "ok"))
        t.append(tuile(f(h["hors_perimetre_avec_reponse"], 0), "hors Code ayant reçu une réponse", "ok"))
    if final:
        t.append(tuile(f(final.get("fr_r_at_1"), 2), "R@1 français (hybride)"))
        t.append(tuile(f(final.get("ar_trad_r_at_1"), 2), "R@1 arabe (traduit)", "att"))
    if calib:
        t.append(tuile(f(calib["etude_12_questions_neuves"]["decision_juste"], 2), "décision juste, 12 questions neuves"))
    if juge:
        t.append(tuile(f(juge["verdict_claude"]["kappa_3_classes"], 2), "κ du LLM-juge (contre Claude)", "att"))
    return carte("Synthèse", "mixte", f'<div class="tuiles">{"".join(t)}</div>' if t else absent("python -m src.rag.evaluer"),
                 "Les tuiles orange signalent une mesure faible ou faite contre une référence non humaine.", large=True)


def bloc_validation() -> str:
    """Où en est la validation humaine : ce qui est relu par un humain, ce qui ne l'est pas."""
    lignes = []

    def ajouter(nom: str, fait: int, total: int, lieu: str) -> None:
        pct = 100.0 * fait / total if total else 0.0
        lignes.append([e(nom), f"{fait} / {total}",
                       f'<span class="piste"><i class="{"ok" if fait == total and total else "att"}" style="width:{pct:.0f}%"></i></span>', f"<code>{e(lieu)}</code>"])

    ng = json_(R / "silver/ner/pregold_dev_fr.json"), json_(R / "silver/ner/pregold_dev_ar.json")
    if all(ng):
        ajouter("NER : phrases du pré-gold relues", sum(x["n_phrases_relues_humain"] for x in ng), sum(x["n_phrases"] for x in ng), "data/a_annoter/ner_dev_*_v1.csv")
    for lot in ("dev", "test"):
        ob = csv_(RACINE / f"data/a_annoter/obligations_{lot}_claude_v1.csv")
        if ob:
            ajouter(f"Obligations {lot} : lignes relues", sum(1 for x in ob if x["statut"] == "verifie"), len(ob), f"data/a_annoter/obligations_{lot}_claude_v1.csv")
    ju = csv_(RACINE / "data/a_annoter/juge_echantillon_v1.csv")
    if ju:
        ajouter("LLM-juge : verdicts humains", sum(1 for x in ju if x["verdict_humain"].strip()), len(ju), "data/a_annoter/juge_echantillon_v1.csv")
    dv = csv_(RACINE / "data/a_annoter/divergences_echantillon_v1.csv")
    if dv:
        ajouter("Divergences : paires relues", sum(1 for x in dv if x["statut"].strip() == "verifie"), len(dv), "data/a_annoter/divergences_echantillon_v1.csv")
    for nom, fich in (("Questions tunisiennes", "questions_tun_v1.csv"), ("Questions arabes traduites", "questions_dev_ar_traduites_v1.csv"),
                      ("Paraphrases", "questions_paraphrases_v1.csv")):
        q = csv_(RACINE / "data/dev" / fich)
        if q:
            ajouter(f"{nom} : validées", sum(1 for x in q if x["statut"].strip() == "verifie"), len(q), f"data/dev/{fich}")
    rs = csv_(R / "silver/llm/resumes_a_noter.csv")
    if rs:
        ajouter("Résumés notés (exactitude, clarté)", sum(1 for x in rs if x.get("exactitude_1_5", "").strip() and x.get("clarte_1_5", "").strip()), len(rs), "reports/silver/llm/resumes_a_noter.csv")
    passations = len(list((RACINE / "etude_utilite/resultats").glob("*_taches.csv"))) if (RACINE / "etude_utilite/resultats").exists() else 0
    lignes.append(["Étude d'utilité : participants", f"{passations} / 12 à 20", '<span class="piste"><i class="att" style="width:0%"></i></span>', "<code>etude_utilite/resultats/</code>"])
    return carte("Validation humaine", "mixte", tableau(["Référence", "Faits", "Avancement", "Fichier"], lignes),
                 "Tant qu'une référence n'est pas relue, les chiffres qui en dépendent mesurent l'accord avec Claude, pas avec un humain.", large=True)


def bloc_alignement() -> str:
    lignes = csv_(R / "silver/alignement/ablations_alignement.csv")
    if not lignes:
        return carte("Alignement AR ↔ FR", "humain", absent("python -m src.alignement_embeddings.evaluer"))
    choix = [x for x in lignes if x["methode"] == "hongrois" and (x["modele"] == "numerotation_seule" or (x["variante"] == "sans_entete" and x["lambda"] in ("0.0", "0.1")))]
    corps = ""
    for x in choix:
        nom = "Numéro d'article seul" if x["modele"] == "numerotation_seule" else f'{x["modele"].split("/")[-1]}, λ = {x["lambda"]}'
        corps += barre(nom, x["precision_gold"], 1.0, f'rappel {f(x["rappel_gold"])}')
    return carte("Alignement AR ↔ FR (précision sur le gold)", "humain", corps,
                 "160 paires vérifiées sur image, tirées parmi les sorties de la numérotation : biais favorable à la méthode hybride. Appariement hongrois, sans en-tête numéroté.")


def bloc_recherche() -> str:
    lignes = csv_(R / "silver/rag/ablations_rag.csv")
    if not lignes:
        return carte("Recherche (RAG)", "mixte", absent("python -m src.rag.evaluer"), large=True)
    sel = [x for x in lignes if x["configuration"].endswith("seuil_par_langue")]
    rows = []
    for x in sel:
        gras = "hybride[multilingual-e5-base]+" in x["configuration"]
        nom = x["configuration"].replace("+seuil_par_langue", "")
        rows.append([f"<b>{e(nom)}</b>" if gras else e(nom), f(x["fr_r_at_1"], 2), f(x["ar_trad_r_at_1"], 2), f(x["tun_r_at_1"], 2),
                     f(x["global_r_at_5"], 2), x["global_abstention_a_tort"], x["global_abstention_correcte_hors"], f(x["global_exactitude_bout_en_bout"], 2)])
    return carte("Recherche : configurations (seuil par langue)", "mixte",
                 tableau(["Configuration", "R@1 FR", "R@1 AR trad.", "R@1 tun.", "R@5 global", "Abst. à tort /48", "Hors refusées /29", "Exactitude"], rows),
                 "77 questions de développement (dev déjà consulté) ; 21 questions arabes traduites par Claude, à valider. En gras : configuration de la démo.", large=True)


def bloc_llm() -> str:
    d = json_(R / "silver/llm/prompting_resultats.json")
    if not d:
        return carte("LLM : stratégies de prompt", "auto", absent("python -m src.rag.evaluer_llm"))
    corps = ""
    for s in d["strategies"]:
        g = s["global"]
        corps += f'<h3>{e(s["strategie"].replace("_", " "))}</h3>' + barre("Référence citée", g["reference_citee"]) + \
                 barre("Citation inventée", g["citation_inventee"], 0.2, classe="mal") + barre("Abstention à tort", g["abstention_a_tort"], 0.5, classe="mal")
    return carte(f'LLM : stratégies de prompt ({d["modele"]})', "auto", corps,
                 "Une seule exécution (les sorties du LLM ne sont pas déterministes). Citation inventée : échelle 0 à 0,2.")


def bloc_audit() -> str:
    a = json_(R / "gold/audit/audit_resultats.json")
    if not a:
        return carte("Audit : hallucinations, abstention, robustesse", "auto", absent("python -m src.audit.audit"), large=True)
    h = a["hallucinations"]
    tuiles = "".join([tuile(f(h["article_invente_affiche"], 0), "article inventé affiché", "ok"), tuile(f(h["hors_perimetre_avec_reponse"], 0), "hors Code répondu", "ok"),
                      tuile(f(h["citation_hors_contexte_brut"], 3), "citation hors contexte (avant filtre)"), tuile(f(h["sans_citation_brut"], 2), "sans citation (avant filtre)")])
    inv = "".join(barre(k.replace(" (original répété)", ""), v["decision"], 1.0, f'n = {v["n"]}', "ref" if k.startswith("bruit") else "") for k, v in a["invariance"].items())
    rows = [[e(k), v["n_dans"], v["n_hors"], f(v.get("fausse_abstention_finale"), 3), f(v.get("reference_citee"), 3), f(v.get("abstention_correcte_hors"), 3)]
            for k, v in a["abstention_par_langue"].items()]
    ec = a["ecart_langues"]
    ecart = barre("Même premier article (FR / AR)", ec["meme_premier_article"]) + barre("Mêmes articles cités", ec["memes_citations"]) + \
        f'<p class="note">Sur {ec["paires"]} paires : juste dans les deux langues {ec["juste_les_deux"]}, en français seulement {ec["juste_fr_seulement"]}, en arabe seulement {ec["juste_ar_seulement"]}.</p>'
    corps = (f'<div class="tuiles">{tuiles}</div><div class="deux"><div><h3>Robustesse (décision identique à l\'original)</h3>{inv}</div>'
             f'<div><h3>Abstention par langue</h3>{tableau(["Langue", "dans", "hors", "Fausse abst. finale", "Réf. citée", "Hors refusé"], rows)}<h3>Écart entre langues</h3>{ecart}</div></div>')
    return carte(f'Audit : hallucinations, abstention, robustesse ({a["n_requetes"]} requêtes, {h["reponses_llm"]} réponses du LLM)', "mixte", corps,
                 "Paraphrases, traductions et variantes écrites par Claude. La ligne grise est le bruit du LLM seul : seuls les écarts au-delà comptent.", large=True)


def bloc_tunisien() -> str:
    d, d7 = json_(R / "gold/tunisien/tunisien_resultats.json"), json_(R / "gold/tunisien/qwen7b/tunisien_resultats.json")
    if not d:
        return carte("Questions en tunisien", "claude", absent("python -m src.tunisien.evaluer"))
    noms = {"directe_fr": "Recherche directe (FR)", "multilingue": "Multilingue direct", "translit_ar": "Translittération vers l'arabe",
            "traduction_fr": "Traduction FR (qwen2.5:3b)", "traduction_ar": "Traduction AR (qwen2.5:3b)"}
    corps = "".join(barre(noms[k], v["global"]["r_at_5"], 1.0, f'R@1 {f(v["global"]["r_at_1"], 2)}') for k, v in d["methodes"].items() if k in noms)
    if d7 and "traduction_fr" in d7.get("methodes", {}):
        v = d7["methodes"]["traduction_fr"]["global"]
        corps += barre("Traduction FR (qwen2.5:7b)", v["r_at_5"], 1.0, f'R@1 {f(v["r_at_1"], 2)}', "fort")
    return carte("Questions en tunisien : R@5 par méthode", "claude", corps,
                 f'{d["n_questions"]} questions (30 dans le Code, 9 hors) ; 24 + 6 écrites par Claude, à valider. Traduire puis chercher bat la recherche multilingue directe.')


def bloc_ner() -> str:
    corps, vu = "", False
    for lg, nom in (("fr", "Français"), ("ar", "Arabe")):
        p = json_(R / f"silver/ner/pregold_dev_{lg}.json")
        if not p:
            continue
        vu = True
        corps += f"<h3>{nom} ({p['n_phrases']} phrases, {p['n_entites']} entités)</h3>"
        for k, s in p["systemes"].items():
            corps += barre(k, s["micro"]["f1"], 1.0, f'souple {f(s["souple"]["f1"])}')
    if not vu:
        return carte("NER : F1 par span", "claude", absent("python -m src.ner_juridique.evaluer_gold --langue fr --accepter-claude"))
    return carte("NER : F1 par span (strict ; souple en détail)", "claude", corps,
                 "Référence = pré-gold de Claude, non relu. L'accord avec les règles (0,89 pour XLM-R FR) surestimait la qualité.")


def bloc_obligations() -> str:
    d = json_(R / "platinum/obligations/evaluation_dev_extracteur.json")
    if not d:
        return carte("Obligations", "claude", absent("python -m src.obligation_extraction.evaluer_obligations --gold data/a_annoter/obligations_dev_claude_v1.csv"), large=True)
    det = d["detection_obligation"]
    modal = "".join(barre(k, v["f1"], 1.0, f'P {f(v["precision"], 2)} · R {f(v["rappel"], 2)}') for k, v in d["modal_par_classe"].items())
    role = "".join(barre(k, v["f1"], 1.0, f'support {v["support_gold"]}', "faible" if v["support_gold"] < 10 else "") for k, v in sorted(d.get("role_par_classe", {}).items(), key=lambda kv: -kv[1]["support_gold"]))
    corps = (f'<div class="tuiles">{tuile(f(det["f1"], 2), "détection obligation (F1)")}{tuile(f(d.get("role_macro_f1"), 2), "F1 macro par rôle", "att")}'
             f'{tuile(f(d.get("role_exactitude_classes"), 2), "exactitude des classes de rôle")}</div>'
             f'<div class="deux"><div><h3>F1 par type (modal)</h3>{modal}</div><div><h3>F1 par rôle</h3>{role}</div></div>')
    return carte(f'Obligations : extracteur de règles ({d["n_commun"]} phrases du dev)', "claude", corps,
                 "Pré-gold de Claude, dev annoté avec les prédictions sous les yeux : chiffres probablement surestimés. Test non mesuré. Barres claires : moins de 10 exemples.", large=True)


def courbe_risque() -> str:
    pts = [x for x in csv_(R / "platinum/abstention/points.csv") if x["jeu"] == "dev"]
    if not pts:
        return ""
    ordre = sorted(pts, key=lambda x: -float(x["cosnorm"]))
    juste = [x["dans"] == "True" and x["bon_top1"] == "True" for x in ordre]
    n, xs, ys, ok = len(ordre), [], [], 0
    for i, j in enumerate(juste, 1):
        ok += j
        xs.append(i / n)
        ys.append(1 - ok / i)
    L, H, mg = 470, 240, 46
    px = lambda v: mg + v * (L - mg - 26)
    py = lambda v: H - mg - v * (H - mg - 10)
    ligne = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
    axes = "".join(f'<line x1="{px(0)}" x2="{px(1)}" y1="{py(t)}" y2="{py(t)}" class="grille"/><text x="{mg - 6}" y="{py(t) + 4}" class="axe" text-anchor="end">{int(t * 100)} %</text>' for t in (0, 0.25, 0.5, 0.75, 1))
    axes += "".join(f'<text x="{px(t)}" y="{H - mg + 16}" class="axe" text-anchor="middle">{int(t * 100)} %</text>' for t in (0, 0.25, 0.5, 0.75, 1))
    return (f'<svg viewBox="0 0 {L} {H}" class="courbe" role="img" aria-label="Courbe risque-couverture">{axes}'
            f'<polyline points="{ligne}" class="trait"/><text x="{px(0.5)}" y="{H - 4}" class="axe" text-anchor="middle">couverture (part des questions auxquelles on répond)</text>'
            f'<text x="10" y="{py(0.5)}" class="axe" transform="rotate(-90 10 {py(0.5)})" text-anchor="middle">risque d\'erreur</text></svg>')


def bloc_abstention() -> str:
    c = json_(R / "platinum/abstention/calibration.json")
    if not c:
        return carte("Abstention calibrée", "mixte", absent("python -m src.platinum.calibration"), large=True)
    d, loo, neuf = c["dev"], c["dev_leave_one_out"], c["etude_12_questions_neuves"]
    rows = [["Dev (seuils réglés dessus)", d["n"], f(d["decision_juste"]), f'[{f(d["ic95_decision_juste"][0], 2)} ; {f(d["ic95_decision_juste"][1], 2)}]', f'{d["fausses_abstentions"]} / {d["n_dans"]}', f'{d["hors_perimetre_repondu"]} / {d["n_hors"]}'],
            ["Dev, leave-one-out", d["n"], f(loo["decision_juste"]), f'[{f(loo["ic95"][0], 2)} ; {f(loo["ic95"][1], 2)}]', f'{loo["fausses_abstentions"]} / {d["n_dans"]}', f'{loo["hors_perimetre_repondu"]} / {d["n_hors"]}'],
            ["<b>12 questions neuves</b>", neuf["n"], f(neuf["decision_juste"]), f'[{f(neuf["ic95_decision_juste"][0], 2)} ; {f(neuf["ic95_decision_juste"][1], 2)}]', f'{neuf["fausses_abstentions"]} / {neuf["n_dans"]}', f'{neuf["hors_perimetre_repondu"]} / {neuf["n_hors"]}']]
    au = c.get("auroc_dev", {})
    corps = (f'<div class="deux"><div>{tableau(["Jeu", "n", "Décision juste", "IC 95 %", "Fausses abstentions", "Hors Code répondu"], rows)}'
             f'<p class="note">AUROC du signal (dans le Code / hors Code) : global {f(au.get("global"), 2)}, français {f(au.get("fr"), 2)}, arabe {f(au.get("ar"), 2)}. '
             f'Seuils : français {f(c["regle"]["seuils"]["fr"], 4)}, arabe {f(c["regle"]["seuils"]["ar"], 4)}.</p></div>'
             f'<div><h3>Courbe risque–couverture (dev)</h3>{courbe_risque()}<p class="note">Risque = réponses fausses ou à une question hors Code, parmi celles données.</p></div></div>')
    return carte("Abstention calibrée", "mixte", corps,
                 "Les 12 questions neuves sont la seule mesure non optimiste, mais petite (intervalle large).", large=True)


def bloc_juge() -> str:
    j7, j3 = json_(R / "gold/juge/accord_qwen2.5_7b.json"), json_(R / "gold/juge/accord_qwen2.5_3b.json")
    if not j7:
        return carte("LLM-juge de fidélité", "claude", absent("python -m src.juge.juge juger --modele qwen2.5:7b"))
    m = j7["verdict_claude"]["matrice"]
    cl = ("fidele", "partiel", "infidele")
    tot = {a: sum(m.get(f"{a}->{b}", 0) for b in cl) or 1 for a in cl}
    cases = "".join(f'<tr><th>{a}</th>' + "".join(f'<td style="--p:{m.get(f"{a}->{b}", 0) / tot[a]:.2f}">{m.get(f"{a}->{b}", 0)}</td>' for b in cl) + "</tr>" for a in cl)
    kap = barre("qwen2.5:7b", j7["verdict_claude"]["kappa_3_classes"], 1.0, f'fidèle/non {f(j7["verdict_claude"]["kappa_fidele_vs_non"], 2)}', "fort")
    if j3:
        kap += barre("qwen2.5:3b", j3["verdict_claude"]["kappa_3_classes"], 1.0, f'fidèle/non {f(j3["verdict_claude"]["kappa_fidele_vs_non"], 2)}')
    humain = "verdict_humain" in j7
    return carte("LLM-juge de fidélité : κ de Cohen", "humain" if humain else "claude",
                 f'<h3>κ à 3 classes</h3>{kap}<h3>Matrice du 7B (lignes : référence ; colonnes : juge)</h3>'
                 f'<table class="matrice"><thead><tr><th></th>{"".join(f"<th>{b}</th>" for b in cl)}</tr></thead><tbody>{cases}</tbody></table>',
                 "Référence = verdicts de Claude sur 56 réponses ; aucun verdict humain enregistré. Le 7B signale toutes les réponses infidèles mais donne des fausses alertes." if not humain else "")


def bloc_divergences() -> str:
    d = json_(R / "gold/divergences/evaluation_detecteur.json")
    if not d:
        return carte("Divergences AR ↔ FR", "claude", absent("python -m src.divergences.evaluer --jugements data/a_annoter/divergences_jugements_claude_v1.json"))
    noms = {"similarite_faible": "Similarité faible", "nombres_differents": "Nombres différents", "temoin_aleatoire": "Témoins au hasard"}
    corps = "".join(barre(noms[k], v["part_problemes"], 1.0, f'n = {v["n"]} · impact juridique {v["avec_impact_juridique"]}') for k, v in d["par_selection"].items())
    reelles = sum(v["part_divergences_reelles"] * v["n"] for v in d["par_selection"].values())
    return carte("Divergences AR ↔ FR : part de paires à problème", "claude", corps,
                 f"Aucune divergence juridique réelle trouvée ({reelles:.0f} sur {d['n']}) : les problèmes sont des défauts d'OCR du texte arabe. Jugements de Claude sur 34 paires.")


def bloc_references() -> str:
    r = json_(R / "platinum/references/resume.json")
    if not r:
        return carte("Références croisées", "auto", absent("python -m src.obligation_extraction.references_croisees"))
    co = r["coherence_ar_fr"]
    rows = [[nom, r[lg]["mentions"], f'{r[lg]["par_type"]["interne"]} / {r[lg]["par_type"]["externe"]} / {r[lg]["par_type"]["relative"]}', r[lg]["cibles_sans_article"], r[lg]["cibles_vers_article_abroge"]]
            for lg, nom in (("fr", "Français"), ("ar", "Arabe"))]
    corps = (tableau(["Langue", "Mentions", "internes / externes / relatives", "Cibles sans article", "Vers un article abrogé"], rows) +
             barre("Renvois identiques en AR et FR", co["taux_identiques"], 1.0, f'{co["identiques"]} / {co["avec_renvoi"]} entrées') +
             '<p class="note">Les écarts sont des défauts d\'OCR probables du texte arabe (art. 87, 100, 125, 176, 227, 265, 287), non confirmés sur image. Précision estimée à 91 % sur 35 mentions relues par Claude.</p>')
    return carte("Références croisées (extraction par règles)", "auto", corps)


def bloc_resume() -> str:
    rs = csv_(R / "silver/llm/resumes_a_noter.csv")
    notes = sum(1 for x in rs if x.get("exactitude_1_5", "").strip() and x.get("clarte_1_5", "").strip())
    corps = f'<div class="tuiles">{tuile(f"{notes} / {len(rs)}", "résumés notés", "att" if notes < len(rs) else "ok")}</div>' if rs else absent("python -m src.rag.evaluer_llm")
    return carte("Résumé en langage clair : grille humaine", "humain", corps,
                 "Exactitude et clarté (1 à 5) : à remplir dans <code>reports/silver/llm/resumes_a_noter.csv</code>. Aucune mesure tant que la grille est vide.")


# ------------------------------------------------------------------ page
CSS = """
:root{--fond:#F5F3EE;--carte:#FBFBF8;--bord:#E4E1D8;--texte:#344054;--texte2:#667085;--marine:#17324D;--ok:#2E7D5B;--att:#B5671B;--mal:#B4412F;--bleu:#2F6FB3;--piste:#E9E6DD}
@media (prefers-color-scheme:dark){:root{--fond:#14171C;--carte:#1C2026;--bord:#2C323B;--texte:#D4D8DE;--texte2:#98A1AE;--marine:#0F2236;--ok:#5DBB93;--att:#E0954A;--mal:#E07A68;--bleu:#6FA6DE;--piste:#2A3039}}
*{box-sizing:border-box}body{margin:0;background:var(--fond);color:var(--texte);font:15px/1.5 "Segoe UI",Tahoma,Arial,sans-serif}
header.page{background:var(--marine);color:#fff;padding:18px 24px}header.page h1{margin:0;font-size:22px}header.page p{margin:4px 0 0;opacity:.85;font-size:13px}header.page code{background:rgba(255,255,255,.16);color:#fff}
.legende{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
main{max-width:1240px;margin:0 auto;padding:18px 16px 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}
.carte{background:var(--carte);border:1px solid var(--bord);border-radius:12px;padding:16px;min-width:0}.carte.large{grid-column:1/-1}
.carte header{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.carte h2{font-size:16px;margin:0;color:var(--texte)}h3{font-size:13px;margin:14px 0 6px;color:var(--texte2);text-transform:uppercase;letter-spacing:.04em}
.badge{font-size:11px;font-weight:600;padding:2px 9px;border-radius:99px;white-space:nowrap;border:1px solid}
.b-h{color:var(--ok);border-color:var(--ok)}.b-c{color:var(--att);border-color:var(--att)}.b-a{color:var(--bleu);border-color:var(--bleu)}.b-m{color:var(--texte2);border-color:var(--texte2)}
.ligne{display:grid;grid-template-columns:minmax(120px,38%) 1fr 52px auto;gap:8px;align-items:center;margin:5px 0;font-size:13px}
.lib{overflow:hidden;text-overflow:ellipsis}.piste{background:var(--piste);border-radius:99px;height:10px;display:block;overflow:hidden}
.piste i{display:block;height:100%;background:var(--bleu);border-radius:99px}.piste i.mal{background:var(--mal)}.piste i.ref{background:var(--texte2)}.piste i.fort,.piste i.ok{background:var(--ok)}.piste i.faible,.piste i.att{background:var(--att);opacity:.7}
.val{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}.det{grid-column:2/-1;color:var(--texte2);font-size:11px;margin-top:-3px}.vide{grid-column:2/-1;color:var(--texte2)}
.tuiles{display:flex;gap:10px;flex-wrap:wrap}.tuile{flex:1 1 150px;border:1px solid var(--bord);border-radius:10px;padding:10px 12px}
.tuile b{display:block;font-size:24px;line-height:1.1}.tuile span{font-size:12px;color:var(--texte2)}.tuile.ok b{color:var(--ok)}.tuile.att b{color:var(--att)}
.deux{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:5px 8px;border-bottom:1px solid var(--bord);text-align:left;vertical-align:middle}th{color:var(--texte2);font-weight:600;font-size:12px}
.defile{overflow-x:auto}.note{color:var(--texte2);font-size:12px;margin:10px 0 0}.absent{color:var(--att)}code{font-size:12px;background:var(--piste);padding:1px 5px;border-radius:4px}
.matrice td{text-align:center;font-variant-numeric:tabular-nums;background:color-mix(in srgb,var(--bleu) calc(var(--p)*70%),transparent)}.matrice th{text-align:center}
.courbe{width:100%;height:auto;max-width:520px}.courbe .trait{fill:none;stroke:var(--bleu);stroke-width:2}.courbe .grille{stroke:var(--bord);stroke-width:1}.courbe .axe{fill:var(--texte2);font-size:10px}
footer{max-width:1240px;margin:0 auto;padding:0 16px 30px;color:var(--texte2);font-size:12px}
"""


def construire() -> str:
    blocs = [bloc_synthese(), bloc_validation(), bloc_alignement(), bloc_recherche(), bloc_llm(), bloc_audit(), bloc_tunisien(),
             bloc_ner(), bloc_obligations(), bloc_references(), bloc_abstention(), bloc_juge(), bloc_divergences(), bloc_resume()]
    legende = "".join(badge(n) for n in ("humain", "claude", "auto", "mixte"))
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Tableau de bord LegalTN</title><style>{CSS}</style></head><body>"
            f'<header class="page"><h1>Tableau de bord d\'évaluation · LegalTN</h1>'
            f"<p>Généré le {date.today().strftime('%d/%m/%Y')}. Les chiffres sont lus dans <code>reports/</code> et <code>data/</code> ; les commentaires sous chaque bloc sont rédigés à la main.</p>"
            f'<div class="legende">{legende}</div></header><main>{"".join(blocs)}</main>'
            f"<footer>LegalTN fournit une information, jamais un conseil juridique. Textes publics ; aucune donnée personnelle. "
            f"Régénérer : <code>python -X utf8 -m src.rapports.tableau_de_bord</code>.</footer></body></html>")


def main() -> None:
    SORTIE.write_text(construire(), encoding="utf-8")
    print("->", SORTIE, f"({SORTIE.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
