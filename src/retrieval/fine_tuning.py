"""Fine-tuning contrastif de l'encodeur e5 sur les paires d'articles FR <-> AR du Code du travail.

Données : les articles présents dans les deux langues (même numéro), lus dans les corpus déjà
utilisés par la démo. Aucune donnée créée : on apprend au modèle que la version française et la
version arabe d'un même article doivent avoir des vecteurs proches.

Protocole (fixé AVANT toute mesure, aucun réglage) :
  - découpage par article, graine 20261115 : 80 % entraînement, 20 % évaluation ; un article
    n'est jamais des deux côtés ;
  - perte MultipleNegativesRankingLoss (les autres articles du lot servent d'exemples négatifs),
    dans les deux sens (FR -> AR et AR -> FR) ;
  - 2 époques, lots de 16, taux d'apprentissage 2e-5, textes tronqués à 256 jetons ;
  - couche de vocabulaire (embeddings de mots, ~192 M paramètres) GELÉE, les 12 couches du
    transformer entraînées ; GPU en demi-précision (AMP) si disponible. Raison : la carte de 4 Go
    ne peut pas contenir l'entraînement complet (poids + gradients + états d'Adam ≈ 4,4 Go) ;
  - 3 graines d'entraînement (13, 42, 2026) ; on rapporte chaque graine, la moyenne et l'écart.

Mesures, avant et après fine-tuning :
  A. alignement sur les 20 % d'articles jamais vus : texte AR -> bon article FR parmi TOUS les
     articles FR (R@1, R@5), et FR -> AR ;
  B. questions du dev v2 (recherche dense croisée FR+AR) : R@1, R@5 par langue.
Limite : les articles visés par les questions du dev peuvent faire partie des 80 % d'entraînement
(paires article-article, pas question-article) ; la mesure B n'est donc pas indépendante.

Usage :
  python -X utf8 src/retrieval/fine_tuning.py --rapports reports/silver/fine_tuning
  python -X utf8 src/retrieval/fine_tuning.py --essai     (petit essai : 1 graine, 10 pas)
"""
import argparse
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src" / "demo"))
sys.path.insert(0, str(RACINE / "src" / "evaluation"))
sys.path.insert(0, str(RACINE / "src"))

MODELE = "intfloat/multilingual-e5-base"
GRAINE_DECOUPAGE = 20261115
GRAINES = [13, 42, 2026]
EPOQUES, LOT, TAUX, LONGUEUR = 2, 16, 2e-5, 256
DEV = RACINE / "data/dev/questions_dev_v2.csv"
EMPREINTE_DEV = "9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8"


# ---------------------------------------------------------------- données
def paires_fr_ar(corpus):
    """Une paire par numéro d'article présent dans les deux langues (premier texte rencontré)."""
    premier = {}
    for lg in ("fr", "ar"):
        for a in corpus[lg].articles:
            premier.setdefault(lg, {}).setdefault(a["article"], a["texte"])
    communs = sorted(set(premier["fr"]) & set(premier["ar"]))
    return [{"article": l, "fr": premier["fr"][l], "ar": premier["ar"][l]} for l in communs]


def decouper(paires, graine=GRAINE_DECOUPAGE, part_eval=0.2):
    labels = [p["article"] for p in paires]
    random.Random(graine).shuffle(labels)
    n_eval = round(len(labels) * part_eval)
    evaluation = set(labels[:n_eval])
    return ([p for p in paires if p["article"] not in evaluation],
            [p for p in paires if p["article"] in evaluation])


# ---------------------------------------------------------------- encodage et mesures
def encoder(modele, textes, prefixe):
    return modele.encode([prefixe + t for t in textes], batch_size=32, normalize_embeddings=True,
                         show_progress_bar=False)


def rappel(vq, labels_q, vd, labels_d):
    """R@1 / R@5 : pour chaque requête, le bon numéro d'article est-il dans les k premiers ?"""
    sims = vq @ vd.T
    r1 = r5 = 0
    for i, lab in enumerate(labels_q):
        ordre, vus = np.argsort(-sims[i]), []
        for j in ordre:
            if labels_d[j] not in vus:
                vus.append(labels_d[j])
            if len(vus) == 5:
                break
        r1 += vus[0] == lab
        r5 += lab in vus
    return {"r1": int(r1), "r5": int(r5), "n": len(labels_q)}


def mesurer(modele, corpus, evaluation, questions):
    tous = {lg: ([a["article"] for a in corpus[lg].articles], [a["texte"] for a in corpus[lg].articles])
            for lg in ("fr", "ar")}
    vec = {lg: encoder(modele, tous[lg][1], "passage: ") for lg in ("fr", "ar")}
    labels_eval = [p["article"] for p in evaluation]
    res = {
        "ar_vers_fr": rappel(encoder(modele, [p["ar"] for p in evaluation], "query: "), labels_eval,
                             vec["fr"], tous["fr"][0]),
        "fr_vers_ar": rappel(encoder(modele, [p["fr"] for p in evaluation], "query: "), labels_eval,
                             vec["ar"], tous["ar"][0]),
    }
    # Questions du dev : recherche croisée FR + AR, meilleur score par article.
    dans = [q for q in questions if q["type"] == "dans_perimetre"]
    vq = encoder(modele, [q["question"] for q in dans], "query: ")
    labels_d = tous["fr"][0] + tous["ar"][0]
    vd = np.vstack([vec["fr"], vec["ar"]])
    par_langue = {}
    for lg in sorted({q["langue"] for q in dans}) + ["toutes"]:
        idx = [i for i, q in enumerate(dans) if lg == "toutes" or q["langue"] == lg]
        par_langue[lg] = rappel(vq[idx], [dans[i]["article_reference"].strip() for i in idx], vd, labels_d)
    res["questions_dev"] = par_langue
    return res


# ---------------------------------------------------------------- entraînement
def entrainer(modele, entrainement, graine, max_pas=None):
    import torch
    from sentence_transformers.losses import MultipleNegativesRankingLoss
    random.seed(graine)
    np.random.seed(graine)
    torch.manual_seed(graine)
    perte = MultipleNegativesRankingLoss(modele)
    for nom, param in modele.named_parameters():
        if "word_embeddings" in nom:
            param.requires_grad = False
    entrainables = [q for q in modele.parameters() if q.requires_grad]
    optim = torch.optim.AdamW(entrainables, lr=TAUX)
    gpu = modele.device.type == "cuda"
    echelle = torch.amp.GradScaler("cuda", enabled=gpu)
    exemples = ([(p["fr"], p["ar"]) for p in entrainement] + [(p["ar"], p["fr"]) for p in entrainement])
    modele.train()
    pas, historique = 0, []
    for epoque in range(EPOQUES):
        random.Random(graine + epoque).shuffle(exemples)
        for i in range(0, len(exemples), LOT):
            lot = exemples[i:i + LOT]
            if len(lot) < 2:
                continue
            a = modele.tokenize(["query: " + x for x, _ in lot])
            b = modele.tokenize(["passage: " + y for _, y in lot])
            # sentence-transformers 6 ajoute des champs non tensoriels : on ne déplace que les tenseurs.
            a = {k: (v.to(modele.device) if hasattr(v, "to") else v) for k, v in a.items()}
            b = {k: (v.to(modele.device) if hasattr(v, "to") else v) for k, v in b.items()}
            with torch.autocast("cuda", dtype=torch.float16, enabled=gpu):
                valeur = perte([a, b], None)
            optim.zero_grad()
            echelle.scale(valeur).backward()
            echelle.step(optim)
            echelle.update()
            historique.append(round(float(valeur.detach()), 4))
            pas += 1
            if max_pas and pas >= max_pas:
                modele.eval()
                return historique
    modele.eval()
    return historique


def charger_modele():
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer(MODELE, device="cuda" if torch.cuda.is_available() else "cpu")
    m.max_seq_length = LONGUEUR
    return m


def main():
    import repondre
    from baseline_bm25 import lire
    p = argparse.ArgumentParser()
    p.add_argument("--rapports", default=str(RACINE / "reports/silver/fine_tuning"))
    p.add_argument("--essai", action="store_true")
    a = p.parse_args()
    if hashlib.sha256(DEV.read_bytes()).hexdigest() != EMPREINTE_DEV:
        raise ValueError("Le dev v2 diffère de la version consignée.")
    corpus = repondre.charger()
    paires = paires_fr_ar(corpus)
    entrainement, evaluation = decouper(paires)
    questions = list(lire(DEV))
    import torch
    print("appareil :", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu", flush=True)
    print(f"paires FR-AR : {len(paires)} ; entraînement {len(entrainement)} ; évaluation {len(evaluation)}", flush=True)

    sortie = Path(a.rapports)
    sortie.mkdir(parents=True, exist_ok=True)
    rapport = {"meta": {"modele": MODELE, "graine_decoupage": GRAINE_DECOUPAGE, "graines": GRAINES,
                        "epoques": EPOQUES, "lot": LOT, "taux": TAUX, "longueur": LONGUEUR,
                        "paires": len(paires), "embeddings_mots_geles": True, "entrainement": len(entrainement),
                        "evaluation": len(evaluation), "articles_evaluation": sorted(p["article"] for p in evaluation),
                        "statut": "developpement_non_independant"}}
    t0 = time.time()
    rapport["avant"] = mesurer(charger_modele(), corpus, evaluation, questions)
    print("avant :", json.dumps(rapport["avant"], ensure_ascii=False), f"({time.time() - t0:.0f} s)", flush=True)

    rapport["apres"] = {}
    for graine in ([GRAINES[0]] if a.essai else GRAINES):
        t0 = time.time()
        modele = charger_modele()
        hist = entrainer(modele, entrainement, graine, max_pas=10 if a.essai else None)
        mesure = mesurer(modele, corpus, evaluation, questions)
        rapport["apres"][str(graine)] = {**mesure, "pertes": hist, "secondes": round(time.time() - t0)}
        print(f"graine {graine} :", json.dumps(mesure, ensure_ascii=False),
              f"perte {hist[0]} -> {hist[-1]} ({time.time() - t0:.0f} s)", flush=True)
        if a.essai:
            break
        del modele

    def serie(cle, sous=None, champ="r1"):
        vals = [(v[cle][sous] if sous else v[cle])[champ] for v in rapport["apres"].values()]
        return {"valeurs": vals, "moyenne": round(statistics.mean(vals), 2),
                "ecart_type": round(statistics.stdev(vals), 2) if len(vals) > 1 else None}
    rapport["resume"] = {f"{cle}_{champ}": serie(cle, champ=champ)
                         for cle in ("ar_vers_fr", "fr_vers_ar") for champ in ("r1", "r5")}
    for lg in rapport["avant"]["questions_dev"]:
        for champ in ("r1", "r5"):
            rapport["resume"][f"dev_{lg}_{champ}"] = serie("questions_dev", lg, champ)
    nom = "essai.json" if a.essai else "resultats.json"
    (sortie / nom).write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rapport["resume"], ensure_ascii=False))


if __name__ == "__main__":
    main()
