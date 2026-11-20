"""LLM-juge : la réponse rédigée est-elle fidèle à l'article qu'elle cite ?

Verdicts : ``fidele`` (tout ce que dit la réponse est dans l'article et répond à la question),
``partiel`` (juste mais incomplète, ou avec un ajout non appuyé), ``infidele`` (contredit
l'article, lui fait dire ce qu'il ne dit pas, ou ne répond pas à la question posée).

Échantillon : réponses de la démo tirées de l'audit Gold (questions originales et paraphrases,
dans le périmètre, réponse donnée), avec le texte des articles cités.

Usage :
  python -X utf8 -m src.juge.juge echantillon
  python -X utf8 -m src.juge.juge juger --modele qwen2.5:7b
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

from src.rag import generer

RACINE = Path(__file__).resolve().parents[2]
AUDIT = RACINE / "reports/gold/audit/audit_details.csv"
ECHANTILLON = RACINE / "data/a_annoter/juge_echantillon_v1.csv"
VERDICTS = ("fidele", "partiel", "infidele")

CONSIGNE = (
    "Tu es un juriste qui vérifie la fidélité d'une réponse au texte du Code du travail tunisien. "
    "On te donne une question, la réponse d'un assistant, et le texte des articles que la réponse cite. "
    "Juge UNIQUEMENT d'après ces articles, pas d'après tes connaissances.\n"
    "- FIDELE : tout ce que dit la réponse est dans les articles, et elle répond à la question.\n"
    "- PARTIEL : la réponse est juste mais incomplète sur un point important, ou ajoute un élément "
    "absent des articles sans le contredire.\n"
    "- INFIDELE : la réponse contredit les articles, leur fait dire ce qu'ils ne disent pas, "
    "ou ne répond pas à la question.\n"
    "Commence ta réponse par exactement un de ces trois mots : FIDELE, PARTIEL ou INFIDELE. "
    "Puis écris « | » et une justification d'une phrase.\n"
    "Exemple : INFIDELE | La réponse donne un délai d'un mois alors que l'article dit une semaine."
)
# Le verdict est le premier des trois mots qui apparaît (préfixe « VERDICT: » toléré) ;
# « INFIDELE » est testé avant « FIDELE » grâce à la frontière de mot.
RE_VERDICT = re.compile(r"\b(INFID[EÈ]LE|FID[EÈ]LE|PARTIEL)\b", re.IGNORECASE)


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def construire_echantillon() -> None:
    from src.rag.recherche import Recherche

    if ECHANTILLON.exists():
        raise SystemExit(f"{ECHANTILLON.name} existe déjà (jugements possibles) : rien réécrit.")
    corpus = Recherche(None).corpus  # sans encodeur : seulement les textes
    index = {lg: {a["article"]: a["texte"] for a in reversed(c.articles)} for lg, c in corpus.items()}
    lignes = [l for l in lire(AUDIT) if l["dans"] == "True" and l["abstention"] == "False"
              and l["llm_appele"] == "True" and l["repetition"] == "0"
              and l["type"] in ("original", "paraphrase")]
    with open(ECHANTILLON, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "source", "type", "langue", "question", "reponse",
                                          "articles_cites", "article_reference", "textes_articles",
                                          "verdict_humain", "verdict_claude", "commentaire"])
        w.writeheader()
        for k, l in enumerate(lignes, 1):
            lg = "ar" if l["langue"].startswith("ar") else "fr"
            cites = [c for c in l["citations"].split(" | ") if c]
            textes = "\n\n".join(f"[Article {c}] {' '.join(index[lg].get(c, '(introuvable)').split())}" for c in cites)
            w.writerow({"id": f"J{k:02d}", "source": l["source"], "type": l["type"], "langue": lg,
                        "question": l["question"], "reponse": l["reponse"], "articles_cites": " | ".join(cites),
                        "article_reference": l["reference"], "textes_articles": textes,
                        "verdict_humain": "", "verdict_claude": "", "commentaire": ""})
    print(f"{len(lignes)} réponses -> {ECHANTILLON}")


def appliquer(jugements: Path) -> None:
    """Écrit les jugements de Claude (JSON id -> [verdict, commentaire]) dans ``verdict_claude``.

    Ne touche jamais à ``verdict_humain``.
    """
    j = json.loads(jugements.read_text(encoding="utf-8"))
    lignes = lire(ECHANTILLON)
    for l in lignes:
        verdict, commentaire = j[l["id"]]
        assert verdict in VERDICTS, (l["id"], verdict)
        l["verdict_claude"] = verdict
        if not l["commentaire"].strip():
            l["commentaire"] = commentaire
    with open(ECHANTILLON, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print({v: sum(l["verdict_claude"] == v for l in lignes) for v in VERDICTS})


def juger_une(question: str, reponse: str, textes: str, modele: str) -> tuple[str, str]:
    messages = [{"role": "system", "content": CONSIGNE},
                {"role": "user", "content": f"Question : {question}\n\nRéponse de l'assistant : {reponse}\n\n"
                                            f"Articles cités :\n{textes[:3500]}"}]
    brut = generer.appeler(messages, modele)
    m = RE_VERDICT.search(brut)
    verdict = m.group(1).upper().replace("È", "E").lower() if m else "illisible"
    return verdict, brut.replace("\n", " ")[:300]


# ---------------------------------------------------------------- accord
def kappa(a: list[str], b: list[str]) -> float:
    """Kappa de Cohen entre deux séries d'étiquettes."""
    n = len(a)
    if not n:
        return float("nan")
    classes = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in classes)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def binaire(v: str) -> str:
    return "fidele" if v == "fidele" else "non_fidele"


def juger(modele: str, sortie: Path) -> None:
    lignes = lire(ECHANTILLON)
    resultats = []
    for l in lignes:
        debut = time.perf_counter()
        verdict, brut = juger_une(l["question"], l["reponse"], l["textes_articles"], modele)
        resultats.append({"id": l["id"], "langue": l["langue"], "verdict_juge": verdict, "justification": brut,
                          "latence_s": round(time.perf_counter() - debut, 1),
                          "verdict_humain": l["verdict_humain"].strip(), "verdict_claude": l["verdict_claude"].strip()})
        print(f"  {l['id']} {verdict}", flush=True)
    sortie.mkdir(parents=True, exist_ok=True)
    nom = modele.replace(":", "_")
    with open(sortie / f"juge_{nom}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resultats[0].keys()))
        w.writeheader()
        w.writerows(resultats)
    accord = {"modele": modele, "n": len(resultats),
              "illisibles": sum(r["verdict_juge"] == "illisible" for r in resultats),
              "distribution_juge": {v: sum(r["verdict_juge"] == v for r in resultats) for v in VERDICTS}}
    for ref in ("verdict_humain", "verdict_claude"):
        paires = [(r[ref], r["verdict_juge"]) for r in resultats if r[ref] in VERDICTS]
        if not paires:
            continue
        a, b = [x for x, _ in paires], [y for _, y in paires]
        accord[ref] = {
            "n": len(paires),
            "accord_brut_3_classes": round(sum(x == y for x, y in paires) / len(paires), 3),
            "kappa_3_classes": round(kappa(a, b), 3),
            "kappa_fidele_vs_non": round(kappa([binaire(x) for x in a], [binaire(y) for y in b]), 3),
            "matrice": {f"{x}->{y}": sum(1 for p in paires if p == (x, y)) for x in VERDICTS for y in VERDICTS + ("illisible",)
                        if any(p == (x, y) for p in paires)},
            "par_langue": {lg: round(kappa([x for (x, _), r in zip(paires, resultats) if r["langue"] == lg],
                                           [y for (_, y), r in zip(paires, resultats) if r["langue"] == lg]), 3)
                           for lg in ("fr", "ar")},
        }
    with open(sortie / f"accord_{nom}.json", "w", encoding="utf-8") as f:
        json.dump(accord, f, ensure_ascii=False, indent=2)
    print(json.dumps(accord, ensure_ascii=False, indent=1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["echantillon", "appliquer", "juger"])
    parser.add_argument("--modele", default="qwen2.5:7b")
    parser.add_argument("--jugements", type=Path, default=RACINE / "data/a_annoter/juge_jugements_claude_v1.json")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/gold/juge")
    args = parser.parse_args()
    if args.action == "echantillon":
        construire_echantillon()
    elif args.action == "appliquer":
        appliquer(args.jugements)
    else:
        juger(args.modele, args.sortie)


if __name__ == "__main__":
    main()
