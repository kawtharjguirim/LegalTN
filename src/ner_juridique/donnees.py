"""Données NER : corpus silver, lots gold corrigés, métriques par span (caractères)."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from .regles import TYPES, depuis_texte

RACINE = Path(__file__).resolve().parents[2]
SILVER = RACINE / "data/silver"
LOTS = {
    ("dev", "fr"): [RACINE / "data/dev/ner_dev_fr_v1.csv", RACINE / "data/a_annoter/ner_dev_fr_v1.csv"],
    ("dev", "ar"): [RACINE / "data/dev/ner_dev_ar_v1.csv", RACINE / "data/a_annoter/ner_dev_ar_v1.csv"],
    ("test", "fr"): [RACINE / "data/test_locked/ner_test_fr_v1.csv", RACINE / "data/a_annoter/ner_test_fr_v1.csv"],
    ("test", "ar"): [RACINE / "data/test_locked/ner_test_ar_v1.csv", RACINE / "data/a_annoter/ner_test_ar_v1.csv"],
}


def charger_silver(langue: str) -> list[dict]:
    with open(SILVER / f"ner_silver_{langue}.jsonl", encoding="utf-8") as f:
        lignes = [json.loads(l) for l in f]
    for l in lignes:
        l["entites"] = [tuple(e) for e in l["entites"]]
    return lignes


def separer_validation(lignes: list[dict], part: float = 0.1, graine: int = 0):
    """Validation silver par article (pour l'arrêt précoce), jamais par phrase."""
    articles = sorted({l["article"] for l in lignes})
    rng = random.Random(graine)
    val = set(rng.sample(articles, max(1, int(len(articles) * part))))
    return [l for l in lignes if l["article"] not in val], [l for l in lignes if l["article"] in val]


def charger_lot(nom: str, langue: str, verifies_seulement: bool = True,
                statuts: tuple[str, ...] = ("verifie",)) -> tuple[list[dict], Path]:
    """Premier fichier existant parmi les emplacements prévus (gelé, puis à annoter).

    ``statuts`` : statuts acceptés comme référence (``verifie`` = relu par un humain ;
    ``verifie_claude`` = annoté par Claude, à n'accepter qu'explicitement)."""
    for chemin in LOTS[(nom, langue)]:
        if chemin.exists():
            break
    else:
        raise FileNotFoundError(f"lot {nom}/{langue} introuvable")
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f))
    if verifies_seulement:
        lignes = [l for l in lignes if l.get("statut", "").strip() in statuts]
    return [{"id": l["item_id"], "phrase": l["phrase"], "entites": depuis_texte(l["entites"]),
             "statut": l.get("statut", "").strip()} for l in lignes], chemin


def f1_chevauchement(gold: list[list], pred: list[list]) -> dict:
    """F1 « souple » : une entité est juste si elle chevauche une entité de même type
    (chaque entité appariée une seule fois). Mesure secondaire, à côté du F1 strict."""
    vp_p = vp_g = n_p = n_g = 0
    for g, p in zip(gold, pred):
        g, p = list(map(tuple, g)), list(map(tuple, p))
        n_g, n_p = n_g + len(g), n_p + len(p)
        libres = list(g)
        for e in p:
            m = next((x for x in libres if x[2] == e[2] and x[0] < e[1] and e[0] < x[1]), None)
            if m:
                libres.remove(m)
                vp_p += 1
        vp_g = vp_p
    pr = vp_p / n_p if n_p else 0.0
    rp = vp_g / n_g if n_g else 0.0
    return {"precision": pr, "rappel": rp, "f1": 2 * pr * rp / (pr + rp) if pr + rp else 0.0}


def f1_spans(gold: list[list], pred: list[list]) -> dict:
    """Correspondance exacte (début, fin, type) ; micro et par type."""
    compte = {t: {"vp": 0, "pred": 0, "gold": 0} for t in TYPES}
    for g, p in zip(gold, pred):
        sg, sp = set(map(tuple, g)), set(map(tuple, p))
        for e in sg:
            compte[e[2]]["gold"] += 1
        for e in sp:
            compte[e[2]]["pred"] += 1
        for e in sg & sp:
            compte[e[2]]["vp"] += 1

    def prf(c):
        p = c["vp"] / c["pred"] if c["pred"] else 0.0
        r = c["vp"] / c["gold"] if c["gold"] else 0.0
        return {"precision": p, "rappel": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
                "n_gold": c["gold"], "n_pred": c["pred"]}

    total = {k: sum(c[k] for c in compte.values()) for k in ("vp", "pred", "gold")}
    par_type = {t: prf(c) for t, c in compte.items()}
    presents = [t for t in TYPES if compte[t]["gold"]]
    return {"micro": prf(total), "par_type": par_type,
            "macro_f1": sum(par_type[t]["f1"] for t in presents) / len(presents) if presents else 0.0}
