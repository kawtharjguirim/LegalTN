"""Baseline BM25 sur le jeu de référence v2 (lecture seule).

- Corpus FR : articles_fr_corrige.csv (questions françaises et tunisiennes).
- Corpus AR : articles_ar.csv (questions arabes).
- Paramètres BM25 standards (k1 = 1,5 ; b = 0,75), non réglés sur le test.
- Mesure : rappel@1 et rappel@5 de l'article de référence (intitulé, suffixe compris).
- Questions hors périmètre (pas d'article de référence) : exclues de la mesure.
- Sortie : data/processed/baseline_bm25_v2_resultats.csv et résumé à l'écran.
"""
import csv, hashlib, math, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
TEST = RACINE / "data" / "test_locked" / "questions_reference_v2.csv"
FR = RACINE / "data" / "processed" / "articles_fr_corrige.csv"
AR = RACINE / "data" / "processed" / "articles_ar.csv"
SORTIE = RACINE / "data" / "processed" / "baseline_bm25_v2_resultats.csv"

K1, B = 1.5, 0.75
K_TOP = 5

STOP_FR = set("""le la les de des du un une et en au aux a l d qu que qui est sont dans par pour
sur ce cet cette ces il elle ils elles ou ne pas se son sa ses leur leurs y s n c j m t ainsi ete etre
avoir plus""".split())
STOP_AR = set("في من على إلى الى عن أن ان هذا هذه التي الذي او أو و ما لا هو هي كان كانت ذلك".split())

SUFFIXES_AR = {"مكرر": "bis", "ثالثا": "ter", "رابعا": "quater"}


def lire(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normaliser_ar(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("ـ", "")
    s = re.sub("[إأآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return s


def tokens(texte, langue):
    if langue == "ar":
        toks, stop = re.findall(r"\w+", normaliser_ar(texte)), STOP_AR
    else:
        toks, stop = re.findall(r"[a-z0-9]+", sans_accents(texte.lower())), STOP_FR
    return [w for w in toks if w not in stop and (len(w) > 1 or w.isdigit())]


def intitule_fr(texte):
    m = re.match(r"\s*Article\s+(\d+)(?:\s+(bis|ter|quater))?", texte or "")
    if not m:
        return None
    return m.group(1) + (" " + m.group(2) if m.group(2) else "")


def intitule_ar(texte):
    m = re.match(r"\s*الفصل\s+(\d+)(?:\s+(مكرر|ثالثا|رابعا))?", texte or "")
    if not m:
        return None
    return m.group(1) + (" " + SUFFIXES_AR[m.group(2)] if m.group(2) else "")


class Bm25:
    def __init__(self, documents):
        # documents : liste de (intitulé, tokens)
        self.docs = documents
        self.n = len(documents)
        self.dl = [len(t) for _, t in documents]
        self.avgdl = sum(self.dl) / self.n
        self.tf = [Counter(t) for _, t in documents]
        self.df = Counter()
        for c in self.tf:
            self.df.update(c.keys())

    def classer(self, requete):
        scores = [0.0] * self.n
        for terme in set(requete):
            if terme not in self.df:
                continue
            idf = math.log(1 + (self.n - self.df[terme] + 0.5) / (self.df[terme] + 0.5))
            for i, c in enumerate(self.tf):
                f = c.get(terme, 0)
                if f:
                    norm = f + K1 * (1 - B + B * self.dl[i] / self.avgdl)
                    scores[i] += idf * f * (K1 + 1) / norm
        ordre = sorted(range(self.n), key=lambda i: -scores[i])
        vus, labels = set(), []
        for i in ordre:
            lab = self.docs[i][0]
            if lab not in vus:
                vus.add(lab)
                labels.append(lab)
            if len(labels) >= K_TOP:
                break
        return labels


def construire(lignes, langue, fonction_intitule):
    docs = []
    for r in lignes:
        lab = fonction_intitule(r["texte_fr" if langue == "fr" else "texte_ar"])
        if lab:
            docs.append((lab, tokens(r["texte_fr" if langue == "fr" else "texte_ar"], langue)))
    return Bm25(docs)


def main():
    print("jeu de référence :", TEST.name, "sha256", hashlib.sha256(TEST.read_bytes()).hexdigest())
    index = {
        "fr": construire(lire(FR), "fr", intitule_fr),
        "ar": construire(lire(AR), "ar", intitule_ar),
    }
    questions = lire(TEST)
    resultats, exclues = [], 0
    for q in questions:
        gold = q["article_reference"].strip()
        if not re.fullmatch(r"\d+(?: bis| ter| quater)?", gold):
            exclues += 1
            continue
        corpus = index["ar"] if q["langue"] == "ar" else index["fr"]
        top = corpus.classer(tokens(q["question"], q["langue"]))
        resultats.append({
            "id": q["id"], "langue": q["langue"], "type": q["type"], "article_attendu": gold,
            "top1": top[0] if top else "", "top5": " | ".join(top),
            "rappel_1": int(bool(top) and top[0] == gold), "rappel_5": int(gold in top),
        })

    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resultats[0].keys()))
        w.writeheader()
        w.writerows(resultats)

    def resume(nom, groupe):
        n = len(groupe)
        if n == 0:
            return
        r1 = sum(x["rappel_1"] for x in groupe)
        r5 = sum(x["rappel_5"] for x in groupe)
        print(f"{nom:<28} n={n:>2}  R@1 = {r1:>2}/{n} = {100*r1/n:5.1f} %   R@5 = {r5:>2}/{n} = {100*r5/n:5.1f} %")

    print(f"questions hors périmètre exclues : {exclues}")
    resume("ensemble", resultats)
    for langue in ("fr", "ar", "tun"):
        resume(f"langue = {langue}", [x for x in resultats if x["langue"] == langue])
    for typ in ("dans_perimetre", "presuppose_faux"):
        resume(f"type = {typ}", [x for x in resultats if x["type"] == typ])
    print(f"sortie : {SORTIE}")


if __name__ == "__main__":
    main()
