"""Effet de la correction SymSpell sur le retrieval, mesuré sur le DEV uniquement.

Quatre conditions : {questions propres, questions avec fautes} x {sans, avec correction}.
- Questions : data/dev/questions_dev_v2.csv (empreinte vérifiée). Aucun fichier de
  data/test_locked/ n'est lu.
- Fautes : générées automatiquement, graine fixe (GRAINE), 1 faute de frappe
  (suppression, substitution, inversion ou insertion d'une lettre) dans au plus
  2 mots de contenu de 5 lettres ou plus par question.
- Système : chaîne de la démo (seuil historique 9,085 inchangé, aucun réglage).
- Mesures : rappel@1 et @5 de l'article de référence (questions dans le périmètre),
  abstentions à tort, refus corrects hors périmètre.

Usage : python -X utf8 src/evaluation/evaluer_correction_dev.py --rapports reports/correction_symspell
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE))
import repondre  # noqa: E402
from baseline_bm25 import STOP_FR, STOP_AR, lire  # noqa: E402

DEV = RACINE / "data" / "dev" / "questions_dev_v2.csv"
EMPREINTE_DEV = "9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8"
GRAINE = 2026
MOTS_FAUTIFS_MAX = 2
LONGUEUR_MIN_FAUTE = 5
ALPHABET = {"fr": "abcdefghijklmnopqrstuvwxyz", "ar": "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"}


def faute(mot: str, rng: random.Random, alphabet: str) -> str:
    """Une seule faute de frappe (distance d'édition 1)."""
    i = rng.randrange(len(mot))
    op = rng.choice(["suppression", "substitution", "inversion", "insertion"])
    if op == "suppression":
        return mot[:i] + mot[i + 1:]
    if op == "substitution":
        return mot[:i] + rng.choice([c for c in alphabet if c != mot[i]]) + mot[i + 1:]
    if op == "inversion" and i < len(mot) - 1:
        return mot[:i] + mot[i + 1] + mot[i] + mot[i + 2:]
    return mot[:i] + rng.choice(alphabet) + mot[i:]


def bruiter(question: str, langue: str, rng: random.Random) -> str:
    stop = STOP_AR if langue == "ar" else STOP_FR
    mots = [m for m in re.finditer(r"[^\W\d_]+", question)
            if len(m.group(0)) >= LONGUEUR_MIN_FAUTE and m.group(0).lower() not in stop]
    choisis = sorted(rng.sample(mots, min(MOTS_FAUTIFS_MAX, len(mots))), key=lambda m: m.start())
    sortie, fin = [], 0
    for m in choisis:
        sortie.append(question[fin:m.start()])
        sortie.append(faute(m.group(0), rng, ALPHABET[langue]))
        fin = m.end()
    return "".join(sortie) + question[fin:]


def mesurer(corpus, questions, champ, corriger):
    dans = [q for q in questions if q["type"] == "dans_perimetre"]
    hors = [q for q in questions if q["type"] == "hors_perimetre"]
    r1 = r5 = faux_abst = refus = modifiees = 0
    details = []
    for q in questions:
        res = repondre.repondre_question(corpus, q[champ], k=5, corriger=corriger)
        labels = [c["article"] for c in res["candidats"]]
        gold = q["article_reference"].strip()
        modifiees += bool(res["corrections"])
        if q["type"] == "dans_perimetre":
            r1 += bool(labels) and labels[0] == gold
            r5 += gold in labels
            faux_abst += res["abstention"]
        else:
            refus += res["abstention"]
        details.append({"id": q["id"], "question": q[champ], "question_corrigee": res["question_corrigee"],
                        "corrections": len(res["corrections"]), "abstention": res["abstention"],
                        "top5": " | ".join(labels), "reference": gold})
    return {
        "rappel_1": round(r1 / len(dans), 3), "rappel_5": round(r5 / len(dans), 3),
        "top1_correct": f"{r1}/{len(dans)}", "top5_correct": f"{r5}/{len(dans)}",
        "abstentions_a_tort": f"{faux_abst}/{len(dans)}",
        "hors_perimetre_refuses": f"{refus}/{len(hors)}",
        "questions_modifiees": f"{modifiees}/{len(questions)}",
    }, details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapports", type=Path, required=True)
    args = parser.parse_args()
    dossier = args.rapports if args.rapports.is_absolute() else RACINE / args.rapports
    if dossier.exists() and any(dossier.iterdir()):
        raise SystemExit(f"{dossier} existe déjà et n'est pas vide : choisir un dossier neuf.")
    # Empreinte calculée avec des fins de ligne CRLF : Git stocke le fichier en LF,
    # ce qui change l'empreinte brute sans changer le contenu.
    octets = DEV.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if hashlib.sha256(octets).hexdigest() != EMPREINTE_DEV:
        raise SystemExit("Le dev v2 diffère de la version consignée.")

    rng = random.Random(GRAINE)
    questions = lire(DEV)
    for q in questions:
        q["question_fautes"] = bruiter(q["question"], repondre.detecter_langue(q["question"]), rng)

    corpus = repondre.charger()
    lignes, tous_details = [], []
    for jeu, champ in [("propres", "question"), ("avec fautes", "question_fautes")]:
        for corriger in (False, True):
            resume, details = mesurer(corpus, questions, champ, corriger)
            condition = f"{jeu} / {'avec' if corriger else 'sans'} correction"
            lignes.append({"condition": condition, **resume})
            tous_details += [{"condition": condition, **d} for d in details]

    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / "tableau_correction_dev.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    with open(dossier / "details_correction_dev.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tous_details[0]))
        w.writeheader()
        w.writerows(tous_details)
    with open(dossier / "evaluation_correction_dev.json", "w", encoding="utf-8") as f:
        json.dump({"jeu": "questions_dev_v2 (développement, non indépendant)", "empreinte_dev": EMPREINTE_DEV,
                   "graine": GRAINE, "mots_fautifs_max": MOTS_FAUTIFS_MAX,
                   "seuil_abstention": repondre.SEUIL_SCORE_MIN, "resultats": lignes},
                  f, ensure_ascii=False, indent=2)

    print(f"{'condition':38} R@1    R@5    top1   top5   abst.tort hors_refusés modifiées")
    for l in lignes:
        print(f"{l['condition']:38} {l['rappel_1']:<6} {l['rappel_5']:<6} {l['top1_correct']:6} "
              f"{l['top5_correct']:6} {l['abstentions_a_tort']:9} {l['hors_perimetre_refuses']:12} "
              f"{l['questions_modifiees']}")
    print(f"Rapports : {dossier}")


if __name__ == "__main__":
    main()
