"""Compare BM25, recherche dense et hybride (RRF) sur le jeu de DÉVELOPPEMENT, par langue.

Lit uniquement data/dev/ (empreinte vérifiée). Refuse tout chemin de data/test_locked/.
Aucun seuil n'est réglé ici : on mesure le classement (R@1, R@5) des questions dans le
périmètre. Les meilleurs scores de toutes les questions (y compris hors périmètre) sont
enregistrés pour choisir plus tard, sur le dev, une règle d'abstention.

Systèmes :
  bm25            BM25 dans la langue détectée, sans seuil (identique à la démo sans seuil)
  dense_meme      encodeur, index de la langue détectée seulement (ablation)
  dense           encodeur, recherche croisée FR + AR
  hybride         RRF(bm25, dense)

Usage :
  python -X utf8 src/evaluation/evaluer_retrieval.py --rapports reports/silver/retrieval_dev
"""
import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src"))
import repondre  # noqa: E402
from baseline_bm25 import lire  # noqa: E402
from retrieval.hybride import classement_bm25, fusion_rrf  # noqa: E402

DEV_V2 = RACINE / "data/dev/questions_dev_v2.csv"
EMPREINTES = {DEV_V2.name: "9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8"}
SYSTEMES = ["bm25", "dense_meme", "dense", "hybride"]


def verifier_jeu(chemin):
    chemin = Path(chemin).resolve()
    if "test_locked" in chemin.parts:
        raise ValueError("Jeu de test gelé : interdit pour le développement.")
    attendu = EMPREINTES.get(chemin.name)
    if attendu and hashlib.sha256(chemin.read_bytes()).hexdigest() != attendu:
        raise ValueError(f"{chemin.name} diffère de la version consignée.")
    return chemin


def classements(question, corpus, index):
    langue = repondre.detecter_langue(question)
    bm = classement_bm25(corpus[langue], question)
    dense_meme = index.classer(question, langues=[langue])
    dense = index.classer(question)
    hyb = fusion_rrf([bm, [lab for lab, _ in dense]])
    return {
        "bm25": bm,
        "dense_meme": [lab for lab, _ in dense_meme],
        "dense": [lab for lab, _ in dense],
        "hybride": [lab for lab, _ in hyb],
    }, {
        "bm25_max": max(corpus[langue].classer(question)[1], default=0.0),
        "dense_max": dense[0][1] if dense else None,
        "hybride_max": hyb[0][1] if hyb else None,
    }


def resumer(lignes):
    groupes = {"toutes": lignes}
    for r in lignes:
        groupes.setdefault(r["langue"], []).append(r)
    res = {}
    for g, rs in groupes.items():
        dans = [r for r in rs if r["dans_perimetre"]]
        res[g] = {"n_dans": len(dans), "n_hors": len(rs) - len(dans)}
        for s in SYSTEMES:
            r1 = sum(r[s][:1] == [r["reference"]] for r in dans)
            r5 = sum(r["reference"] in r[s][:5] for r in dans)
            res[g][s] = {"r1": r1, "r5": r5}
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeu", default=str(DEV_V2))
    p.add_argument("--modele", default=None)
    p.add_argument("--rapports", required=True)
    a = p.parse_args()
    jeu = verifier_jeu(a.jeu)

    from retrieval.dense import IndexDense, MODELE_DEFAUT
    modele = a.modele or MODELE_DEFAUT
    corpus = repondre.charger()
    t0 = time.time()
    index = IndexDense(corpus, modele)
    t_index = time.time() - t0

    lignes = []
    t0 = time.time()
    for q in lire(jeu):
        cl, scores = classements(q["question"], corpus, index)
        lignes.append({
            "id": q["id"], "langue": q["langue"], "dans_perimetre": q["type"] == "dans_perimetre",
            "reference": q["article_reference"].strip(),
            **{s: cl[s][:5] for s in SYSTEMES}, **scores,
        })
    t_req = (time.time() - t0) / max(len(lignes), 1)

    resume = resumer(lignes)
    sortie = Path(a.rapports)
    sortie.mkdir(parents=True, exist_ok=True)
    meta = {"jeu": jeu.name, "sha256_jeu": hashlib.sha256(jeu.read_bytes()).hexdigest(),
            "modele": modele, "k_rrf": 60, "statut": "developpement_non_independant",
            "secondes_index": round(t_index, 1), "secondes_par_question": round(t_req, 3)}
    (sortie / "resultats.json").write_text(json.dumps({"meta": meta, "resume": resume, "questions": lignes},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    with open(sortie / "resume_par_langue.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["langue", "n_dans", "systeme", "r1", "r5"])
        for g, d in resume.items():
            for s in SYSTEMES:
                w.writerow([g, d["n_dans"], s, d[s]["r1"], d[s]["r5"]])

    print(json.dumps(meta, ensure_ascii=False))
    for g, d in resume.items():
        if not d["n_dans"]:
            print(f"{g:7} : 0 question dans le périmètre (non mesurable)")
            continue
        cols = "  ".join(f"{s} R@1 {d[s]['r1']}/{d['n_dans']} R@5 {d[s]['r5']}/{d['n_dans']}" for s in SYSTEMES)
        print(f"{g:7} : {cols}")


if __name__ == "__main__":
    main()
