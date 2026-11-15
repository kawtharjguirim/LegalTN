"""Fine-tuning NER (encodeurs) et baselines, 3 graines, F1 par span.

Systèmes comparés, entraînés sur le corpus silver (annoté par règles) :
- ``regles``  : les règles elles-mêmes (aucun apprentissage) ;
- ``crf``     : CRF du Bronze (traits orthographiques, ``src/ner_crf``) sur mots ;
- encodeurs   : CamemBERT (FR), AraBERT v2 (AR), XLM-R base (FR et AR).

Évaluation : lot dev corrigé à la main (lignes ``statut = verifie``). Tant qu'aucune
ligne n'est vérifiée, seule la validation silver (accord avec les règles) est
calculée : ce n'est PAS une mesure de qualité. ``--test`` évalue le lot test gelé :
à n'utiliser qu'une fois, pour les résultats finaux.

Usage : python -X utf8 -m src.ner_juridique.entrainer --langue fr --modeles crf camembert xlmr
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
from pathlib import Path

from .donnees import RACINE, charger_lot, charger_silver, f1_spans, separer_validation
from .regles import TYPES, annoter

ENCODEURS = {
    "camembert": "almanach/camembert-base",
    "arabert": "aubmindlab/bert-base-arabertv02",
    "xlmr": "FacebookAI/xlm-roberta-base",
}
ETIQUETTES = ["O"] + [f"{p}-{t}" for t in TYPES for p in ("B", "I")]
E2I = {e: i for i, e in enumerate(ETIQUETTES)}
GRAINES = (13, 42, 2026)


# ------------------------------------------------------------------ conversions
def etiquettes_tokens(offsets: list[tuple[int, int]], entites) -> list[int]:
    """Étiquette BIO de chaque token d'après les spans en caractères (-100 : spéciaux)."""
    sortie = []
    for d, f in offsets:
        if d == f:
            sortie.append(-100)
            continue
        lab = "O"
        for ed, ef, t in entites:
            if d >= ed and f <= ef:
                # Le token qui ouvre l'entité est B, les suivants I.
                lab = ("B-" if d == ed else "I-") + t
                break
        sortie.append(E2I[lab])
    return sortie


def spans_depuis_tokens(offsets, labels: list[str], phrase: str) -> list[tuple[int, int, str]]:
    spans, cur = [], None
    for (d, f), lab in zip(offsets, labels):
        if d == f:
            continue
        if lab.startswith("B-") or (lab.startswith("I-") and (cur is None or cur[2] != lab[2:])):
            if cur:
                spans.append(cur)
            cur = [d, f, lab[2:]]
        elif lab.startswith("I-") and cur:
            cur[1] = f
        else:
            if cur:
                spans.append(cur)
            cur = None
    if cur:
        spans.append(cur)
    propres = []
    for d, f, t in spans:
        while d < f and phrase[d].isspace():
            d += 1
        propres.append((d, f, t))
    return propres


def representables(tok, phrases) -> float:
    """Part des entités gold dont les bornes tombent sur des bornes de tokens."""
    n = ok = 0
    for p in phrases:
        enc = tok(p["phrase"], return_offsets_mapping=True, truncation=True, max_length=192)
        debuts = {d for d, f in enc["offset_mapping"] if d != f}
        fins = {f for d, f in enc["offset_mapping"] if d != f}
        # Les tokenizers SentencePiece incluent souvent l'espace initial dans l'offset.
        debuts |= {d + 1 for d in debuts}
        for d, f, _ in p["entites"]:
            n += 1
            ok += d in debuts and f in fins
    return ok / n if n else 1.0


# ------------------------------------------------------------------ encodeurs
def entrainer_encodeur(nom_hf: str, train, val, graine: int, epoques: int = 6,
                       lr: float = 3e-5, lot: int = 16, max_len: int = 192):
    import torch
    from torch.utils.data import DataLoader
    from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                              DataCollatorForTokenClassification, get_linear_schedule_with_warmup,
                              set_seed)

    set_seed(graine)
    appareil = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(nom_hf)
    modele = AutoModelForTokenClassification.from_pretrained(
        nom_hf, num_labels=len(ETIQUETTES), id2label=dict(enumerate(ETIQUETTES)),
        label2id=E2I).to(appareil)

    def encoder(lignes):
        donnees = []
        for l in lignes:
            enc = tok(l["phrase"], return_offsets_mapping=True, truncation=True, max_length=max_len)
            labels = etiquettes_tokens(enc.pop("offset_mapping"), l["entites"])
            donnees.append({**enc, "labels": labels})
        return donnees

    collate = DataCollatorForTokenClassification(tok)
    gen = torch.Generator().manual_seed(graine)
    chargeur = DataLoader(encoder(train), batch_size=lot, shuffle=True, collate_fn=collate,
                          generator=gen)
    optim = torch.optim.AdamW(modele.parameters(), lr=lr, weight_decay=0.01)
    pas = epoques * len(chargeur)
    sched = get_linear_schedule_with_warmup(optim, int(0.1 * pas), pas)
    scaler = torch.amp.GradScaler(enabled=appareil == "cuda")

    meilleur, etat = -1.0, None
    for _ in range(epoques):
        modele.train()
        for b in chargeur:
            b = {k: v.to(appareil) for k, v in b.items()}
            with torch.autocast(appareil, dtype=torch.float16, enabled=appareil == "cuda"):
                perte = modele(**b).loss
            optim.zero_grad()
            scaler.scale(perte).backward()
            scaler.unscale_(optim)
            torch.nn.utils.clip_grad_norm_(modele.parameters(), 1.0)
            scaler.step(optim)
            scaler.update()
            sched.step()
        f1 = f1_spans([l["entites"] for l in val],
                      predire_encodeur(modele, tok, val, max_len))["micro"]["f1"]
        if f1 > meilleur:
            meilleur = f1
            etat = {k: v.detach().cpu().clone() for k, v in modele.state_dict().items()}
    modele.load_state_dict(etat)
    return modele, tok


def predire_encodeur(modele, tok, lignes, max_len: int = 192):
    import torch

    modele.eval()
    appareil = next(modele.parameters()).device
    sorties = []
    with torch.no_grad():
        for l in lignes:
            enc = tok(l["phrase"], return_offsets_mapping=True, truncation=True,
                      max_length=max_len, return_tensors="pt")
            offsets = [tuple(o) for o in enc.pop("offset_mapping")[0].tolist()]
            logits = modele(**{k: v.to(appareil) for k, v in enc.items()}).logits[0]
            labels = [ETIQUETTES[i] for i in logits.argmax(-1).tolist()]
            sorties.append(spans_depuis_tokens(offsets, labels, l["phrase"]))
    return sorties


# ------------------------------------------------------------------ CRF (Bronze)
RE_MOT = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def mots(phrase: str):
    return [(m.group(), m.start(), m.end()) for m in RE_MOT.finditer(phrase)]


def entrainer_crf(train):
    from src.ner_crf.features import phrases_vers_X
    from src.ner_crf.pipeline import entrainer_crf as fit

    def vers_conll(l):
        sortie = []
        for w, d, f in mots(l["phrase"]):
            lab = "O"
            for ed, ef, t in l["entites"]:
                if d >= ed and f <= ef:
                    lab = ("B-" if d == ed else "I-") + t
            sortie.append((w, "", lab))
        return sortie

    phrases = [vers_conll(l) for l in train]
    return fit(phrases_vers_X(phrases), [[t[2] for t in s] for s in phrases])


def predire_crf(crf, lignes):
    from src.ner_crf.features import phrases_vers_X

    sorties = []
    for l in lignes:
        ws = mots(l["phrase"])
        labels = crf.predict(phrases_vers_X([[(w, "", "O") for w, _, _ in ws]]))[0] if ws else []
        sorties.append(spans_depuis_tokens([(d, f) for _, d, f in ws], labels, l["phrase"]))
    return sorties


# ------------------------------------------------------------------ boucle
def resumer(valeurs: list[float]) -> dict:
    return {"moyenne": statistics.mean(valeurs),
            "ecart_type": statistics.stdev(valeurs) if len(valeurs) > 1 else 0.0,
            "valeurs": valeurs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--langue", choices=["fr", "ar"], required=True)
    parser.add_argument("--modeles", nargs="+", default=["regles", "crf", "xlmr"])
    parser.add_argument("--epoques", type=int, default=6)
    parser.add_argument("--test", action="store_true", help="Évaluer le lot test gelé (une fois).")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/silver/ner")
    args = parser.parse_args()

    silver = charger_silver(args.langue)
    eval_nom = "test" if args.test else "dev"
    gold, chemin_gold = charger_lot(eval_nom, args.langue)
    print(f"{len(silver)} phrases silver ; {len(gold)} phrases {eval_nom} vérifiées ({chemin_gold.name})")

    resultats = {"langue": args.langue, "evaluation": eval_nom, "n_gold": len(gold),
                 "fichier_gold": chemin_gold.name, "systemes": {}}
    for nom in args.modeles:
        par_graine = []
        graines = (0,) if nom == "regles" else GRAINES
        for graine in graines:
            train, val = separer_validation(silver, graine=graine)
            debut = time.perf_counter()
            if nom == "regles":
                pred_val = [annoter(l["phrase"], args.langue) for l in val]
                pred_gold = [annoter(l["phrase"], args.langue) for l in gold]
                extra = {}
            elif nom == "crf":
                crf = entrainer_crf(train)
                pred_val, pred_gold = predire_crf(crf, val), predire_crf(crf, gold)
                extra = {}
            else:
                modele, tok = entrainer_encodeur(ENCODEURS[nom], train, val, graine, args.epoques)
                pred_val = predire_encodeur(modele, tok, val)
                pred_gold = predire_encodeur(modele, tok, gold)
                extra = {"spans_gold_representables": representables(tok, gold or val)}
                del modele
            mesure = {"graine": graine, "duree_s": round(time.perf_counter() - debut, 1),
                      "accord_regles_val_silver": f1_spans([l["entites"] for l in val], pred_val),
                      **extra}
            if gold:
                mesure["gold"] = f1_spans([l["entites"] for l in gold], pred_gold)
            par_graine.append(mesure)
            cle = "gold" if gold else "accord_regles_val_silver"
            print(f"  {nom:10s} graine {graine:4d}  F1 micro ({cle}) = "
                  f"{mesure[cle]['micro']['f1']:.3f}  [{mesure['duree_s']} s]")
        cle = "gold" if gold else "accord_regles_val_silver"
        resultats["systemes"][nom] = {
            "graines": par_graine,
            "f1_micro": resumer([m[cle]["micro"]["f1"] for m in par_graine]),
            "f1_macro": resumer([m[cle]["macro_f1"] for m in par_graine]),
            "mesure_sur": cle,
        }
    args.sortie.mkdir(parents=True, exist_ok=True)
    fichier = args.sortie / f"ner_{args.langue}_{eval_nom}.json"
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    print(f"-> {fichier}")


if __name__ == "__main__":
    main()
