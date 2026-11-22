"""Gold - transfert vers le tunisien / arabizi / arabe : mesure sur les 50 questions annotées.

Jeu : data/raw/arabic/questions_gold_premiere_revue.csv (questions candidates proposées par IA,
validées et étiquetées par l'utilisateur ; plusieurs articles acceptés par question).
Catégories :
- avec_article : dans le périmètre, au moins un article attendu -> R@1 / R@5 (succès si un article accepté)
- sans_article : sujet du travail mais aucun article du Code ne répond -> l'abstention est la bonne réponse
- hors : hors périmètre -> l'abstention est la bonne réponse
Systèmes : BM25 (langue détectée), dense e5 (croisé), hybride RRF, seuil BM25 9,085, RAG P2V.
Aucun réglage : tous les paramètres sont ceux fixés sur le dev Silver.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path[:0] = ["src", "src/demo", "src/evaluation"]
import repondre  # noqa: E402
from rag import rag  # noqa: E402
from retrieval.hybride import classement_bm25, fusion_rrf  # noqa: E402

JEU = Path("data/raw/arabic/questions_gold_premiere_revue.csv")


def articles_acceptes(champ):
    """« 14 bis ; 6-3 ; 376 et suivants » -> {'14 bis', '6', '376', ..., '390'}."""
    acc = set()
    for brut in champ.split(";"):
        t = brut.strip()
        if not t:
            continue
        m = re.match(r"(\d+)(?:-\d+)?\s*(bis|ter|quater)?(\s+et suivants)?", t)
        if not m:
            continue
        n, suf, suiv = m.group(1), m.group(2), m.group(3)
        acc.add(f"{n} {suf or ''}".strip())
        if suiv:  # convention documentée : « et suivants » = les 14 articles qui suivent
            acc.update(str(int(n) + i) for i in range(1, 15))
    return acc


def lire_jeu(chemin):
    lignes = []
    for r in csv.DictReader(open(chemin, encoding="utf-8-sig")):
        q = (r["question_corrigee (si besoin)"] or "").strip() or r["question"].strip()
        acc = articles_acceptes(r["article_attendu"] or "")
        hors = (r["hors_perimetre (oui/non)"] or "").strip().lower() == "oui"
        cat = "hors" if hors else ("avec_article" if acc else "sans_article")
        lignes.append({"id": r["id"], "langue": r["langue"], "question": q, "acceptes": sorted(acc), "categorie": cat})
    return lignes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rapports", default="reports/gold/transfert")
    p.add_argument("--sans-rag", action="store_true")
    p.add_argument("--traduire", action="store_true", help="couche de traduction du dialecte (src/traduction/dialecte.py)")
    a = p.parse_args()
    from retrieval.dense import IndexDense, MODELE_DEFAUT
    corpus = repondre.charger()
    index = IndexDense(corpus, MODELE_DEFAUT)
    jeu = lire_jeu(JEU)
    t0 = time.time()
    if a.traduire:
        import time as _t
        from traduction import dialecte
        a.rapports = a.rapports.rstrip("/") + "_traduction"
    for q in jeu:
        if a.traduire:
            tr = dialecte.traduire(q["question"])
            q["traduction"] = {k: tr[k] for k in ("question", "traduite", "source", "erreur")}
            if tr["source"] not in ("aucune", "cache"):
                _t.sleep(6)  # quota gratuit
            q["question_origine"], q["question"] = q["question"], tr["question"]
        lg = repondre.detecter_langue(q["question"])
        bm = classement_bm25(corpus[lg], q["question"])
        dense = [lab for lab, _ in index.classer(q["question"])]
        hyb = [lab for lab, _ in fusion_rrf([bm, dense])]
        scores = corpus[lg].classer(q["question"])[1]
        q.update({"langue_detectee": lg, "bm25": bm[:5], "dense": dense[:5], "hybride": hyb[:5],
                  "seuil_abstient": (max(scores, default=0.0) < repondre.SEUIL_SCORE_MIN)})
        if not a.sans_rag:
            r = rag.repondre_rag(q["question"], corpus, "P2V")
            q["rag"] = {k: r.get(k) for k in ("passages", "articles_cites", "abstention", "rejet", "reponse", "erreur")}
        print(q["id"], q["categorie"], q["bm25"][:1], q.get("rag", {}).get("articles_cites"),
              q.get("rag", {}).get("abstention"), flush=True)

    resume = {}
    for g in ["toutes", "tunisien", "arabizi", "arabe"]:
        qs = [q for q in jeu if g == "toutes" or q["langue"] == g]
        avec = [q for q in qs if q["categorie"] == "avec_article"]
        sans = [q for q in qs if q["categorie"] != "avec_article"]
        d = {"n_avec_article": len(avec), "n_sans_article": sum(q["categorie"] == "sans_article" for q in qs),
             "n_hors": sum(q["categorie"] == "hors" for q in qs)}
        for s in ("bm25", "dense", "hybride"):
            d[s] = {"r1": sum(bool(set(q[s][:1]) & set(q["acceptes"])) for q in avec),
                    "r5": sum(bool(set(q[s][:5]) & set(q["acceptes"])) for q in avec)}
        d["seuil_bm25"] = {"abstention_correcte": sum(q["seuil_abstient"] for q in sans),
                           "fausse_abstention": sum(q["seuil_abstient"] for q in avec)}
        if not a.sans_rag:
            d["rag_p2v"] = {
                "bon_article_cite": sum(not q["rag"]["abstention"] and bool(set(q["rag"]["articles_cites"]) & set(q["acceptes"])) for q in avec),
                "fausse_abstention": sum(bool(q["rag"]["abstention"]) for q in avec),
                "abstention_correcte": sum(bool(q["rag"]["abstention"]) for q in sans),
                "erreurs_llm": sum(bool(q["rag"].get("erreur")) for q in qs)}
        resume[g] = d
    meta = {"jeu": str(JEU), "sha256_jeu": hashlib.sha256(JEU.read_bytes()).hexdigest(),
            "origine": "questions proposees par IA, validees et etiquetees par l'utilisateur",
            "modele_dense": MODELE_DEFAUT, "modele_rag": rag.MODELE_DEFAUT, "seuil_bm25": repondre.SEUIL_SCORE_MIN,
            "convention_et_suivants": "+14 articles", "secondes": round(time.time() - t0)}
    out = Path(a.rapports)
    out.mkdir(parents=True, exist_ok=True)
    (out / "resultats.json").write_text(json.dumps({"meta": meta, "resume": resume, "questions": jeu},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    print(json.dumps(resume, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
