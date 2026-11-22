"""Gold - LLM-juge de fidelite des reponses RAG, a valider contre une annotation humaine.

Pour chaque reponse RAG non abstenue (variante P2V), le juge recoit la question, la reponse et le
texte des articles cites, et dit si la reponse est FIDELE (tout ce qu'elle affirme est dans l'article)
et si elle REPOND a la question. Le juge n'est jamais utilise comme verite : il est valide par kappa
contre l'annotation humaine (fiche reports/gold/llm_juge/annotation_humaine.csv).
Meme modele local que le RAG (qwen2.5:3b) : biais d'auto-evaluation possible, a discuter.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "src/demo"]
import repondre  # noqa: E402
from rag import rag  # noqa: E402

SYSTEME = (
    "Tu es un évaluateur strict de réponses juridiques. On te donne une question, une réponse et le texte "
    "des articles cités du Code du travail tunisien. Juge uniquement à partir de ces textes. "
    "\"fidele\" = true seulement si TOUT ce que la réponse affirme est dit par les articles fournis. "
    "\"repond\" = true si la réponse répond bien à la question posée. "
    "Réponds uniquement par un objet JSON : {\"fidele\": true|false, \"repond\": true|false, \"justification\": \"...\"}"
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--resultats", default="reports/gold/rag_p2v_apres_correction/resultats.json")
    p.add_argument("--sortie", default="reports/gold/llm_juge")
    a = p.parse_args()
    corpus = repondre.charger()
    textes = {}
    for lg in ("fr", "ar"):
        for x in corpus[lg].articles:
            textes.setdefault(x["article"], {})[lg] = x["texte"]
    d = json.loads(Path(a.resultats).read_text(encoding="utf-8"))
    questions = {}
    for row in csv.DictReader(open("data/dev/questions_dev_v2.csv", encoding="utf-8")):
        questions[row["id"]] = row["question"]
    items = []
    for l in d["questions"]:
        s = l["sorties"]["P2V"]
        if s["abstention"]:
            continue
        arts = "\n\n".join(f"[Article {k}]\n" + textes.get(k, {}).get("fr" if l["langue"] == "fr" else "ar",
                           textes.get(k, {}).get("fr", ""))[:rag.MAX_CARACTERES] for k in s["articles_cites"])
        msg = [{"role": "system", "content": SYSTEME},
               {"role": "user", "content": f"Question : {questions[l['id']]}\n\nRéponse : {s['reponse']}\n\nArticles cités :\n{arts}"}]
        v = {}
        for _ in range(3):  # erreurs HTTP intermittentes d'Ollama : 3 essais, sinon erreur comptee
            try:
                v = json.loads(rag.appeler_llm(msg, json_impose=True))
                break
            except (OSError, json.JSONDecodeError) as e:
                v = {"erreur": type(e).__name__, "detail": str(e)[:200]}
        items.append({"id": l["id"], "langue": l["langue"], "question": questions[l["id"]], "reponse": s["reponse"],
                      "articles_cites": s["articles_cites"], "reference": l["reference"], "juge": v})
        print(l["id"], v.get("fidele"), v.get("repond"), flush=True)
    out = Path(a.sortie)
    out.mkdir(parents=True, exist_ok=True)
    (out / "juge_sorties.json").write_text(json.dumps({"modele_juge": rag.MODELE_DEFAUT, "source": a.resultats,
                                                       "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "annotation_humaine.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "reponse", "articles_cites", "fidele_humain (oui/non)",
                    "repond_humain (oui/non)", "commentaire"])
        for it in items:
            w.writerow([it["id"], it["question"], it["reponse"], " ; ".join(it["articles_cites"]), "", "", ""])


if __name__ == "__main__":
    main()
