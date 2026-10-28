"""Contrôle de la démo sur questions_dev_v2, sans réglage ni lecture des tests.

Compare la règle historique à 9,085 à la même récupération sans seuil de score.
Les références de ce dev sont héritées : ce n'est pas un test indépendant.
Sortie JSON sur stdout, aucun fichier d'entrée ou annotation modifié.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src/demo"))
import repondre
from baseline_bm25 import lire

DEV = RACINE / "data/dev/questions_dev_v2.csv"
EMPREINTE_DEV = "9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8"


def erreur(dans_perimetre, gold, abstention, labels):
    if not dans_perimetre:
        return None if abstention else "hors_perimetre_accepte"
    if abstention:
        return "abstention_a_tort"
    if labels and labels[0] == gold:
        return None
    return "article_voisin_classe_devant" if gold in labels else "reference_absente_top5"


def resumer(lignes, variante):
    dans = [r for r in lignes if r["dans_perimetre"]]
    hors = [r for r in lignes if not r["dans_perimetre"]]
    r1 = sum(bool(r[variante]["articles"]) and r[variante]["articles"][0] == r["reference"] for r in dans)
    r5 = sum(r["reference"] in r[variante]["articles"] for r in dans)
    return {
        "questions": len(lignes), "dans_perimetre": len(dans), "hors_perimetre": len(hors),
        "article_top1_correct": r1, "article_dans_top5": r5,
        "rappel_article_1": r1 / len(dans) if dans else None,
        "rappel_article_5": r5 / len(dans) if dans else None,
        "abstentions_a_tort": sum(r[variante]["abstention"] for r in dans),
        "abstentions_correctes_hors_perimetre": sum(r[variante]["abstention"] for r in hors),
        "reponses_fournies": sum(not r[variante]["abstention"] for r in lignes),
        "erreurs_par_categorie": dict(Counter(
            r[variante]["erreur"] for r in lignes if r[variante]["erreur"]
        )),
    }


def evaluer():
    if hashlib.sha256(DEV.read_bytes()).hexdigest() != EMPREINTE_DEV:
        raise ValueError("Le dev v2 diffère de la version consignée ; vérifier sa provenance.")
    corpus = repondre.charger()
    lignes = []
    for q in lire(DEV):
        if q["type"] not in {"dans_perimetre", "hors_perimetre"}:
            raise ValueError(f"Type de question non géré : {q['id']}")
        dans = q["type"] == "dans_perimetre"
        gold = q["article_reference"].strip()
        if dans and not gold:
            raise ValueError(f"Référence absente pour la question dans le périmètre : {q['id']}")
        langue = repondre.detecter_langue(q["question"])
        c = corpus[langue]
        ordre, _, termes = c.classer(q["question"])
        abstention_sans_seuil = not termes or not any(t in c.bm.df for t in termes)
        labels = []
        if not abstention_sans_seuil:
            for i in ordre:
                label = c.articles[i]["article"]
                if label not in labels:
                    labels.append(label)
                if len(labels) == 5:
                    break
        avec = c.repondre(q["question"], k=5)
        labels_avec = [r["article"] for r in avec["candidats"]]
        lignes.append({
            "id": q["id"], "question": q["question"], "langue_reference": q["langue"],
            "langue_routee": langue, "dans_perimetre": dans, "reference": gold,
            "sans_seuil_score": {
                "abstention": abstention_sans_seuil, "articles": labels,
                "erreur": erreur(dans, gold, abstention_sans_seuil, labels),
            },
            "seuil_historique": {
                "abstention": avec["abstention"], "articles": labels_avec,
                "erreur": erreur(dans, gold, avec["abstention"], labels_avec),
            },
        })
    variantes = ("sans_seuil_score", "seuil_historique")
    sources = (
        "src/evaluation/baseline_bm25.py", "src/demo/repondre.py",
        "src/evaluation/evaluer_dev_reprise.py", "data/dev/questions_dev_v2.csv",
        "data/processed/articles_ar.csv", "data/processed/articles_fr_corrige.csv",
    )
    return {
        "nature": "Contrôle sur développement déjà consulté ; aucune performance indépendante.",
        "reglage_effectue": False,
        "references": "Questions et réponses attendues héritées ; aucune nouvelle annotation humaine.",
        "definition_erreur": "Hors périmètre accepté, abstention à tort ou premier article incorrect.",
        "configuration": {
            "seuil_historique": repondre.SEUIL_SCORE_MIN,
            "stop_tun_actif": repondre.ACTIVER_STOP_TUN,
            "sans_seuil": "Même classement et abstention si aucun terme connu ; seul le seuil de score est omis.",
        },
        "empreintes": {nom: hashlib.sha256((RACINE / nom).read_bytes()).hexdigest() for nom in sources},
        "global": {v: resumer(lignes, v) for v in variantes},
        "par_langue": {
            langue: {v: resumer([r for r in lignes if r["langue_reference"] == langue], v) for v in variantes}
            for langue in sorted({r["langue_reference"] for r in lignes})
        },
        "erreurs_evitees": [
            r["id"] for r in lignes if r["sans_seuil_score"]["erreur"] and not r["seuil_historique"]["erreur"]
        ],
        "erreurs_introduites": [
            r["id"] for r in lignes if not r["sans_seuil_score"]["erreur"] and r["seuil_historique"]["erreur"]
        ],
        "details": lignes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapports", type=Path, help="Nouveau dossier pour le JSON et les tableaux de développement.")
    args = parser.parse_args()
    if args.rapports is not None and args.rapports.exists():
        parser.error("Le dossier de rapports existe déjà ; choisir un nouveau dossier.")
    rapport = evaluer()
    if args.rapports is not None:
        args.rapports.mkdir(parents=True)

        def ecrire_csv(nom, lignes, champs):
            with (args.rapports / nom).open("x", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=champs)
                writer.writeheader()
                writer.writerows(lignes)

        commun = {"jeu": "questions_dev_v2", "usage": "developpement_non_independant"}
        mesures = [
            "questions", "dans_perimetre", "hors_perimetre", "article_top1_correct",
            "article_dans_top5", "rappel_article_1", "rappel_article_5",
            "abstentions_a_tort", "abstentions_correctes_hors_perimetre", "reponses_fournies",
        ]
        tableau1 = [
            {**commun, "variante": v, **{k: bilan[k] for k in mesures},
             "erreurs": sum(bilan["erreurs_par_categorie"].values())}
            for v, bilan in rapport["global"].items()
        ]
        ecrire_csv("tableau1_demo_dev.csv", tableau1, [*commun, "variante", *mesures, "erreurs"])
        tableau2 = [
            {**commun, "langue": langue, "variante": v, **{k: bilan[k] for k in mesures}}
            for langue, variantes in rapport["par_langue"].items() for v, bilan in variantes.items()
        ]
        ecrire_csv("tableau2_langues_dev.csv", tableau2, [*commun, "langue", "variante", *mesures])
        erreurs = [
            {**commun, "id": r["id"], "variante": v, "langue": r["langue_reference"],
             "question": r["question"], "reference": r["reference"] if r["dans_perimetre"] else "abstention",
             "abstention": r[v]["abstention"], "articles": " | ".join(r[v]["articles"]),
             "categorie": r[v]["erreur"]}
            for r in rapport["details"] for v in rapport["global"] if r[v]["erreur"]
        ]
        ecrire_csv("erreurs_dev.csv", erreurs, [
            *commun, "id", "variante", "langue", "question", "reference", "abstention", "articles", "categorie",
        ])
        tableau3 = [
            {**commun, "variante": v, "categorie": categorie, "nombre": nombre,
             "erreurs_variante": sum(bilan["erreurs_par_categorie"].values()),
             "exemple_id": next(e["id"] for e in erreurs if e["variante"] == v and e["categorie"] == categorie)}
            for v, bilan in rapport["global"].items()
            for categorie, nombre in bilan["erreurs_par_categorie"].items()
        ]
        ecrire_csv("tableau3_erreurs_dev.csv", tableau3, [
            *commun, "variante", "categorie", "nombre", "erreurs_variante", "exemple_id",
        ])
        with (args.rapports / "evaluation_demo_dev_v2.json").open("x", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(json.dumps(rapport, ensure_ascii=True, indent=2))
