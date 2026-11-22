"""Gold - biais entre langues et robustesse INV (invariance a la langue / au registre).

Aucun nouvel appel de modèle : relit les sorties déjà mesurées.
- Groupes : questions sur le même sujet (même ensemble d'articles acceptés) en tunisien, arabizi, arabe
  (jeu Gold), plus la question française du dev dont l'article de référence est dans cet ensemble.
- Biais : taux de succès par langue sur les MÊMES sujets (comparaison appariée).
- INV : pour un sujet, le système donne-t-il le même 1er article / la même décision RAG dans toutes les langues ?
"""
import json
from collections import defaultdict
from pathlib import Path

GOLD = Path("reports/gold/transfert/resultats.json")
DEV_RET = Path("reports/silver/retrieval_dev/resultats.json")
DEV_RAG = Path("reports/silver/rag_dev/resultats.json")
SORTIE = Path("reports/gold/biais_langues.json")


def main():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))["questions"]
    dev_ret = {q["id"]: q for q in json.loads(DEV_RET.read_text(encoding="utf-8"))["questions"]}
    dev_rag = {q["id"]: q for q in json.loads(DEV_RAG.read_text(encoding="utf-8"))["questions"]}

    sujets = defaultdict(dict)
    for q in gold:
        if q["categorie"] != "avec_article":
            continue
        cle = tuple(q["acceptes"])
        sujets[cle].setdefault(q["langue"], {
            "id": q["id"], "hyb_top1": q["hybride"][:1], "hyb_r5": bool(set(q["hybride"][:5]) & set(cle)),
            "rag_ok": (not q["rag"]["abstention"]) and bool(set(q["rag"]["articles_cites"]) & set(cle)),
            "rag_abst": bool(q["rag"]["abstention"])})
    for i, r in dev_ret.items():
        if r["langue"] != "fr" or not r["dans_perimetre"] or i not in dev_rag:
            continue
        for cle in sujets:
            if r["reference"] in cle and "fr" not in sujets[cle]:
                s = dev_rag[i]["sorties"]["P2V"]
                sujets[cle]["fr"] = {"id": i, "hyb_top1": r["hybride"][:1], "hyb_r5": bool(set(r["hybride"][:5]) & set(cle)),
                                     "rag_ok": (not s["abstention"]) and bool(set(s["articles_cites"]) & set(cle)),
                                     "rag_abst": bool(s["abstention"])}

    langues = ["fr", "arabe", "tunisien", "arabizi"]
    complets = {k: v for k, v in sujets.items() if all(l in v for l in langues)}
    biais = {l: {"n": len(complets), "hyb_r5": sum(v[l]["hyb_r5"] for v in complets.values()),
                 "rag_ok": sum(v[l]["rag_ok"] for v in complets.values())} for l in langues}
    inv_top1 = sum(len({tuple(v[l]["hyb_top1"]) for l in langues}) == 1 for v in complets.values())
    inv_rag = sum(len({(v[l]["rag_ok"], v[l]["rag_abst"]) for l in langues}) == 1 for v in complets.values())
    # paires sans exiger le français
    trio = {k: v for k, v in sujets.items() if all(l in v for l in ["arabe", "tunisien", "arabizi"])}
    out = {"sujets_total": len(sujets), "sujets_4_langues": len(complets),
           "biais_par_langue_memes_sujets": biais,
           "inv_meme_top1_hybride_4_langues": inv_top1, "inv_meme_decision_rag_4_langues": inv_rag,
           "sujets_3_langues_ar": len(trio),
           "biais_3_langues_ar": {l: {"n": len(trio), "hyb_r5": sum(v[l]["hyb_r5"] for v in trio.values()),
                                      "rag_ok": sum(v[l]["rag_ok"] for v in trio.values())}
                                  for l in ["arabe", "tunisien", "arabizi"]},
           "detail": {" ; ".join(k): v for k, v in complets.items()}}
    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}, ensure_ascii=False, indent=1))
    for k, v in complets.items():
        print(" ; ".join(k), {l: (v[l]["id"], v[l]["hyb_r5"], v[l]["rag_ok"]) for l in langues})


if __name__ == "__main__":
    main()
