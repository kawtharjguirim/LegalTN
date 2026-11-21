"""Classification de domaine par fine-tuning LoRA de multilingual-e5-base (têtes de classification + adaptateurs
de rang 8 sur les projections « query » et « value »), même protocole que ``evaluer.py`` (5 plis par blocs).

Pour chaque pli : un modèle appris sur le français et un sur l'arabe, chacun testé dans sa langue **et** dans
l'autre (transfert). Une graine seulement par défaut (coût sur la carte de 4 Go) : l'écart-type de la
comparaison est donc celui, plus large, de la différence entre plis non estimé ici.

Usage : python -X utf8 -m src.domaine.lora [--graine 0] [--epoques 8]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score
from torch.utils.data import DataLoader

from .etiquettes import DOMAINES, charger
from .evaluer import BLOC, MODELE, PLIS, macro, plis

RACINE = Path(__file__).resolve().parents[2]
LONGUEUR = 256


def encoder(tokenizer, textes: list[str]) -> dict:
    return tokenizer(["query: " + t for t in textes], truncation=True, max_length=LONGUEUR, padding=True, return_tensors="pt")


def entrainer(textes: list[str], etiquettes: list[int], epoques: int, graine: int, lot: int = 8, lr: float = 3e-4):
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.manual_seed(graine)
    np.random.seed(graine)
    tok = AutoTokenizer.from_pretrained(MODELE)
    base = AutoModelForSequenceClassification.from_pretrained(MODELE, num_labels=len(DOMAINES))
    modele = get_peft_model(base, LoraConfig(task_type="SEQ_CLS", r=8, lora_alpha=16, lora_dropout=0.1, target_modules=["query", "value"]))
    modele.to("cuda")
    comptes = np.bincount(etiquettes, minlength=len(DOMAINES)).astype(float)
    poids = torch.tensor(len(etiquettes) / (len(DOMAINES) * np.maximum(comptes, 1)), dtype=torch.float, device="cuda")  # classes équilibrées
    opt = torch.optim.AdamW([p for p in modele.parameters() if p.requires_grad], lr=lr, weight_decay=0.01)
    total = epoques * ((len(textes) + lot - 1) // lot)
    plan = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.1 * total)) * max(0.0, 1 - s / total))
    scaler = torch.amp.GradScaler("cuda")
    idx = np.arange(len(textes))
    modele.train()
    for _ in range(epoques):
        np.random.shuffle(idx)
        for d in range(0, len(idx), lot):
            b = idx[d:d + lot]
            enc = {k: v.to("cuda") for k, v in encoder(tok, [textes[i] for i in b]).items()}
            y = torch.tensor([etiquettes[i] for i in b], device="cuda")
            with torch.autocast("cuda", dtype=torch.float16):
                logits = modele(**enc).logits
            perte = torch.nn.functional.cross_entropy(logits.float(), y, weight=poids)
            opt.zero_grad()
            scaler.scale(perte).backward()
            scaler.step(opt)
            scaler.update()
            plan.step()
    modele.eval()
    return modele, tok


@torch.no_grad()
def predire(modele, tok, textes: list[str]) -> list[int]:
    sortie = []
    for d in range(0, len(textes), 16):
        enc = {k: v.to("cuda") for k, v in encoder(tok, textes[d:d + 16]).items()}
        with torch.autocast("cuda", dtype=torch.float16):
            sortie += modele(**enc).logits.argmax(-1).tolist()
    return sortie


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graine", type=int, default=0)
    parser.add_argument("--epoques", type=int, default=8)
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/domaine/lora.json")
    args = parser.parse_args()
    fr, ar = charger("fr"), charger("ar")
    langues = {"fr": fr, "ar": ar}
    idx = {d: i for i, d in enumerate(DOMAINES)}
    y = {lg: np.array([idx[a["domaine"]] for a in art]) for lg, art in langues.items()}
    txt = {lg: [a["texte"] for a in art] for lg, art in langues.items()}
    num = {lg: np.array([a["numero"] for a in art]) for lg, art in langues.items()}
    pli = plis(sorted(set(num["fr"]) | set(num["ar"])), args.graine)
    f = {lg: np.array([pli[n // BLOC] for n in num[lg]]) for lg in langues}
    pred = {(a, b): np.full(len(langues[b]), -1) for a in langues for b in langues}      # (appris sur a, testé sur b)
    debut = time.perf_counter()
    for k in range(PLIS):
        for lg in langues:
            tr = np.flatnonzero(f[lg] != k)
            modele, tok = entrainer([txt[lg][i] for i in tr], [int(y[lg][i]) for i in tr], args.epoques, args.graine + k)
            for cible in langues:
                te = np.flatnonzero(f[cible] == k)
                pred[(lg, cible)][te] = predire(modele, tok, [txt[cible][i] for i in te])
            del modele
            torch.cuda.empty_cache()
            print(f"pli {k + 1}/{PLIS} appris sur {lg} : {time.perf_counter() - debut:.0f} s", flush=True)
    res = {"graine": args.graine, "epoques": args.epoques, "modele": MODELE, "lora": {"r": 8, "alpha": 16, "cibles": ["query", "value"]}, "systemes": {}}
    for (a, b), p in pred.items():
        nom = f"lora_{a}" if a == b else f"lora_transfert_{a}_vers_{b}"
        yy = y[b]
        res["systemes"][nom] = {"macro_f1": round(macro([DOMAINES[i] for i in yy], [DOMAINES[i] for i in p]), 4),
                                "exactitude": round(float(accuracy_score(yy, p)), 4)}
    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res["systemes"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
