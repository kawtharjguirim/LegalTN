"""Gold - question de recherche n°1 du PDF :
« Le retrieval après traduction de la question vers l'arabe standard bat-il le retrieval direct
pour des questions tunisiennes ? »

Expérience d'évaluation seulement : l'application n'est pas modifiée.
Pour chaque question tunisienne / arabizi du jeu Gold, le LLM local (qwen2.5:3b, température 0)
réécrit la question en arabe standard ; on compare ensuite la recherche (BM25, e5, hybride) et le
RAG P2V sur la question directe (mesure déjà faite) et sur la question réécrite.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path[:0] = ["src", "src/demo", "src/evaluation"]
import repondre  # noqa: E402
from rag import rag  # noqa: E402
from retrieval.hybride import classement_bm25, fusion_rrf  # noqa: E402

SOURCE = Path("reports/gold/transfert/resultats.json")
SORTIE = Path("reports/gold/traduction_puis_recherche")
sys.path.insert(0, "src/gold")
CONSIGNE = ("Réécris la question suivante, écrite en dialecte tunisien (lettres arabes ou latines/arabizi), "
            "en arabe standard moderne clair, sans répondre et sans ajouter d'information. "
            "Donne uniquement la question réécrite.")


def main():
    global SORTIE
    p = argparse.ArgumentParser()
    p.add_argument("--traducteur", choices=["ollama", "gemini"], default="ollama")
    a = p.parse_args()
    import llm_juge
    llm_juge.charger_env()
    modele_trad = "gemini-3.1-flash-lite" if a.traducteur == "gemini" else rag.MODELE_DEFAUT
    if a.traducteur == "gemini":
        SORTIE = SORTIE.with_name(SORTIE.name + "_gemini")

    def traduire(msgs):
        if a.traducteur == "gemini":
            for _ in range(4):
                try:
                    out = llm_juge.appeler_gemini(msgs, modele_trad, json_mime=False)
                    time.sleep(6)
                    return out
                except OSError:
                    time.sleep(30)
            raise OSError("Gemini indisponible")
        return rag.appeler_llm(msgs)
    from retrieval.dense import IndexDense, MODELE_DEFAUT
    d = json.loads(SOURCE.read_text(encoding="utf-8"))
    corpus = repondre.charger()
    index = IndexDense(corpus, MODELE_DEFAUT)
    lignes, t0 = [], time.time()
    for q in d["questions"]:
        if q["langue"] not in ("tunisien", "arabizi"):
            continue
        msa = traduire([{"role": "system", "content": CONSIGNE},
                               {"role": "user", "content": q["question"]}]).strip()
        lg = repondre.detecter_langue(msa)
        bm = classement_bm25(corpus[lg], msa)
        dense = [lab for lab, _ in index.classer(msa)]
        hyb = [lab for lab, _ in fusion_rrf([bm, dense])]
        r = rag.repondre_rag(msa, corpus, "P2V")
        lignes.append({"id": q["id"], "langue": q["langue"], "categorie": q["categorie"], "acceptes": q["acceptes"],
                       "question": q["question"], "question_msa": msa, "langue_detectee_msa": lg,
                       "direct": {"bm25": q["bm25"], "dense": q["dense"], "hybride": q["hybride"], "rag": q["rag"]},
                       "traduit": {"bm25": bm[:5], "dense": dense[:5], "hybride": hyb[:5],
                                   "rag": {k: r.get(k) for k in ("articles_cites", "abstention", "rejet", "erreur")}}})
        print(q["id"], "|", msa, "|", hyb[:3], r.get("articles_cites"), r.get("abstention"), flush=True)

    def mesurer(ls, mode):
        avec = [l for l in ls if l["categorie"] == "avec_article"]
        sans = [l for l in ls if l["categorie"] != "avec_article"]
        m = {"n_avec": len(avec), "n_sans": len(sans)}
        for s in ("bm25", "dense", "hybride"):
            m[s + "_r5"] = sum(bool(set(l[mode][s][:5]) & set(l["acceptes"])) for l in avec)
        rg = lambda l: l[mode]["rag"]  # noqa: E731
        m["rag_bon_article"] = sum((not rg(l)["abstention"]) and bool(set(rg(l)["articles_cites"] or []) & set(l["acceptes"])) for l in avec)
        m["rag_fausse_abstention"] = sum(bool(rg(l)["abstention"]) for l in avec)
        m["rag_abstention_correcte"] = sum(bool(rg(l)["abstention"]) for l in sans)
        return m

    resume = {}
    for g in ("tunisien", "arabizi", "les_deux"):
        ls = [l for l in lignes if g == "les_deux" or l["langue"] == g]
        resume[g] = {"direct": mesurer(ls, "direct"), "traduit": mesurer(ls, "traduit")}
    SORTIE.mkdir(parents=True, exist_ok=True)
    meta = {"source": str(SOURCE), "traducteur": a.traducteur, "modele_traduction": modele_trad, "temperature": 0, "graine": rag.GRAINE,
            "consigne": CONSIGNE, "secondes": round(time.time() - t0)}
    (SORTIE / "resultats.json").write_text(json.dumps({"meta": meta, "resume": resume, "questions": lignes},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resume, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
