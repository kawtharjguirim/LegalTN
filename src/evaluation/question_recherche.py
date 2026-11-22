"""Gold - question de recherche : la citation obligatoire reduit-elle les hallucinations
sans augmenter les refus injustifies ?

Relit les sorties RAG deja mesurees (aucun nouvel appel au LLM) et compare les variantes
question par question, avec un bootstrap apparie (10 000 tirages, graine 2026).

Definitions (par question) :
- reponse non fondee : le systeme repond (pas d'abstention) alors que
  * hors perimetre : aucune source du Code n'existe ;
  * dans le perimetre : l'article de reference n'est pas cite.
- refus injustifie : abstention sur une question dans le perimetre.
"""
import argparse
import json
import random
from pathlib import Path


def indicateurs(l, v):
    s = l["sorties"][v]
    repond = not s["abstention"]
    if l["dans_perimetre"]:
        non_fondee = repond and l["reference"] not in s["articles_cites"]
        refus = s["abstention"]
    else:
        non_fondee, refus = repond, False
    return int(non_fondee), int(refus)


def bootstrap(diffs, n=10000, graine=2026):
    rng = random.Random(graine)
    m = len(diffs)
    moy = sorted(sum(rng.choice(diffs) for _ in range(m)) / m for _ in range(n))
    return moy[int(0.025 * n)], moy[int(0.975 * n)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--resultats", default="reports/silver/rag_dev/resultats.json")
    p.add_argument("--sortie", default="reports/gold/question_recherche.json")
    a = p.parse_args()
    lignes = json.loads(Path(a.resultats).read_text(encoding="utf-8"))["questions"]
    variantes = ["P0", "P1", "P2", "P3", "P2V"]
    res = {}
    for v in variantes:
        nf = [indicateurs(l, v)[0] for l in lignes]
        rf = [indicateurs(l, v)[1] for l in lignes if l["dans_perimetre"]]
        res[v] = {"n": len(lignes), "reponses_non_fondees": sum(nf), "n_dans": len(rf), "refus_injustifies": sum(rf)}
    comparaisons = {}
    for ref in ("P0", "P1"):
        for v in ("P2", "P2V"):
            d_nf = [indicateurs(l, v)[0] - indicateurs(l, ref)[0] for l in lignes]
            dans = [l for l in lignes if l["dans_perimetre"]]
            d_rf = [indicateurs(l, v)[1] - indicateurs(l, ref)[1] for l in dans]
            comparaisons[f"{v}_vs_{ref}"] = {
                "delta_non_fondees": sum(d_nf), "ic95_taux_non_fondees": bootstrap(d_nf),
                "delta_refus_injustifies": sum(d_rf), "ic95_taux_refus": bootstrap(d_rf)}
    out = {"source": a.resultats, "bootstrap": {"tirages": 10000, "graine": 2026},
           "par_variante": res, "comparaisons": comparaisons}
    Path(a.sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(a.sortie).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
