"""Démo de bout en bout : question brute -> article le plus pertinent, ou abstention.

Chaîne : détection de la langue -> correction orthographique SymSpell (src/correction) -> BM25 sur le corpus (FR ou AR) -> règle d'abstention -> article cité.
Aucun LLM, aucune API payante. La réponse est un extrait de l'article cité, pas une réponse rédigée.

Usage :
  python3 src/demo/repondre.py "Quel est le délai de préavis pour rompre un CDI ?"
  python3 src/demo/repondre.py                 (saisie interactive)
  python3 src/demo/repondre.py --evaluer       (mesure sur questions_reference_v2.csv, lecture seule)

Règle d'abstention : abstention si aucun terme de contenu de la question n'apparaît dans le corpus de la
langue détectée, ou si le meilleur score BM25 est inférieur à SEUIL_SCORE_MIN (seuil choisi sur le dev).
"""
import csv, math, re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
from baseline_bm25 import (Bm25, K1, B, TEST, FR, AR, intitule_fr, intitule_ar, lire, tokens)

SORTIE = RACINE / "data" / "processed" / "demo_bout_en_bout_v2_resultats.csv"
# Règle d'abstention figée : choisie sur data/dev/questions_dev_v1.csv (13 dans / 15 hors), milieu de la plage
# 9,04-9,13 qui donne 13/15 hors périmètre refusés et 0 fausse abstention sur le dev. Ne pas régler sur le test.
SEUIL_SCORE_MIN = 9.085
# Mots vides tunisiens (translittération latine), ajoutés côté requête seulement. Désactivés par défaut :
# leur activation se décide sur dev (src/evaluation/choisir_regle_abstention_v4.py), jamais sur test.
STOP_TUN = set("ken chnowa chkoun kifech win ch7al el fel fil mta3 mta3ou 3la fi lazem yemken iy le lé "
               "bl w wela 3andou 3andi 9adech 9adhiya mouch ma ysir yeji".split())
ACTIVER_STOP_TUN = False
MESSAGE_ABSTENTION = ("Je ne peux pas répondre à cette question avec le Code du travail disponible : "
                      "elle ne correspond à aucun article de ce corpus. Consultez un professionnel.")


class Corpus:
    def __init__(self, chemin, langue, intitule, col_texte):
        self.langue = langue
        self.articles = []  # métadonnées alignées sur les documents indexés
        docs = []
        for r in lire(chemin):
            texte = r[col_texte].strip()
            lab = intitule(texte)
            if not lab:
                continue
            self.articles.append({"article": lab, "texte": texte, "page": r["page"]})
            docs.append((lab, tokens(texte, langue)))
        self.bm = Bm25(docs)

    def classer(self, question):
        """Retourne (indices triés par score, scores, termes de la question)."""
        requete = tokens(question, self.langue)
        if ACTIVER_STOP_TUN:
            requete = [t for t in requete if t not in STOP_TUN]
        bm = self.bm
        scores = [0.0] * bm.n
        for terme in set(requete):
            if terme not in bm.df:
                continue
            idf = math.log(1 + (bm.n - bm.df[terme] + 0.5) / (bm.df[terme] + 0.5))
            for i, c in enumerate(bm.tf):
                f = c.get(terme, 0)
                if f:
                    norm = f + K1 * (1 - B + B * bm.dl[i] / bm.avgdl)
                    scores[i] += idf * f * (K1 + 1) / norm
        ordre = sorted(range(bm.n), key=lambda i: -scores[i])
        return ordre, scores, requete

    def repondre(self, question, k=3):
        ordre, scores, requete = self.classer(question)
        aucun_terme = not requete or not any(t in self.bm.df for t in requete)
        trop_faible = not scores or max(scores) < SEUIL_SCORE_MIN
        if aucun_terme or trop_faible:
            return {"abstention": True, "langue": self.langue, "candidats": []}
        candidats, vus = [], set()
        for i in ordre:
            art = self.articles[i]
            if art["article"] in vus:
                continue
            vus.add(art["article"])
            candidats.append({**art, "score": round(scores[i], 2)})
            if len(candidats) == k:
                break
        return {"abstention": False, "langue": self.langue, "candidats": candidats}


def detecter_langue(question):
    return "ar" if re.search(r"[؀-ۿ]", question) else "fr"


def repondre_question(corpus, question, k=3, corriger=True):
    """Chaîne complète : langue -> correction SymSpell -> BM25 -> abstention.

    Corpus.repondre (BM25 seul) reste inchangé : c'est la baseline sans correction.
    """
    langue = detecter_langue(question)
    if corriger:
        sys.path.insert(0, str(RACINE))
        from src.correction.correcteur_symspell import correcteur
        correction = correcteur().corriger(question, langue)
    else:
        correction = {"question_originale": question, "question_corrigee": question, "corrections": []}
    resultat = corpus[langue].repondre(correction["question_corrigee"], k=k)
    return {**correction, **resultat}


def charger():
    return {
        "fr": Corpus(FR, "fr", intitule_fr, "texte_fr"),
        "ar": Corpus(AR, "ar", intitule_ar, "texte_ar"),
    }


def afficher(question, resultat):
    print(f"Question : {question}")
    if resultat.get("corrections"):
        print(f"Vouliez-vous dire : {resultat['question_corrigee'].rstrip(' ?')} ?")
    if resultat["abstention"]:
        print(MESSAGE_ABSTENTION)
        return
    meilleur = resultat["candidats"][0]
    print(f"Article le plus pertinent : article {meilleur['article']} (page PDF {meilleur['page']})")
    print(f"Texte : {meilleur['texte'][:600]}{' ...' if len(meilleur['texte']) > 600 else ''}")
    autres = ", ".join(f"article {c['article']} (score {c['score']})" for c in resultat["candidats"][1:])
    if autres:
        print(f"Autres candidats : {autres}")
    print("Note : extrait de l'article cité, sans reformulation par un modèle.")


def evaluer(corpus):
    print("jeu de référence :", TEST.name)
    lignes, abst_hors, faux_abst, n_hors, n_dans = [], 0, 0, 0, 0
    r1 = r5 = 0
    for q in lire(TEST):
        langue = "ar" if q["langue"] == "ar" else "fr"
        res = corpus[langue].repondre(q["question"], k=5)
        gold = q["article_reference"].strip()
        attendu_article = bool(re.fullmatch(r"\d+(?: bis| ter| quater)?", gold))
        if attendu_article:
            n_dans += 1
            labels = [c["article"] for c in res["candidats"]]
            hit1 = int(bool(labels) and labels[0] == gold)
            hit5 = int(gold in labels)
            r1 += hit1
            r5 += hit5
            if res["abstention"]:
                faux_abst += 1
        else:
            n_hors += 1
            if res["abstention"]:
                abst_hors += 1
        lignes.append({
            "id": q["id"], "langue": q["langue"], "type": q["type"], "article_attendu": gold,
            "abstention": int(res["abstention"]),
            "top1": res["candidats"][0]["article"] if res["candidats"] else "",
        })
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print(f"dans le périmètre (n = {n_dans}) : R@1 = {r1}/{n_dans}, R@5 = {r5}/{n_dans}, "
          f"abstention à tort = {faux_abst}/{n_dans}")
    print(f"hors périmètre (n = {n_hors}) : abstention = {abst_hors}/{n_hors}")
    print(f"sortie : {SORTIE}")


def main():
    corpus = charger()
    if "--evaluer" in sys.argv:
        evaluer(corpus)
        return
    question = " ".join(a for a in sys.argv[1:] if not a.startswith("--")).strip() or input("Question : ").strip()
    if not question:
        print("Question vide.")
        return
    if "--historique" in sys.argv:          # chaîne de la correction seule (expérience SymSpell)
        resultat = repondre_question(corpus, question, corriger="--sans-correction" not in sys.argv)
    else:                                   # pipeline complet (src/pipeline/traitement.py)
        sys.path.insert(0, str(RACINE))
        from src.pipeline.traitement import pipeline
        resultat = pipeline().repondre(question)
        if "--debug" in sys.argv:
            for e in resultat["etapes"]:
                print(f"  [{e['etape']}] {e['sortie']}")
    afficher(question, resultat)


if __name__ == "__main__":
    main()
