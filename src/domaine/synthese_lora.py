"""Synthèse des exécutions LoRA (une par graine) : moyenne et écart-type, écrits dans ``lora_synthese.json``.

Entrées : ``reports/platinum/domaine/lora.json`` (graine 0) et ``lora_graine1.json``, ``lora_graine2.json``.

Usage : python -X utf8 -m src.domaine.synthese_lora
"""

from __future__ import annotations

import json
import statistics as st
from pathlib import Path

DOSSIER = Path(__file__).resolve().parents[2] / "reports/platinum/domaine"
FICHIERS = ("lora.json", "lora_graine1.json", "lora_graine2.json")


def synthese() -> dict:
    runs = [json.loads((DOSSIER / f).read_text(encoding="utf-8")) for f in FICHIERS if (DOSSIER / f).exists()]
    if not runs:
        raise SystemExit("Aucune exécution LoRA trouvée.")
    res = {"graines": [r["graine"] for r in runs], "n_graines": len(runs), "systemes": {}}
    for nom in runs[0]["systemes"]:
        m = [r["systemes"][nom]["macro_f1"] for r in runs]
        a = [r["systemes"][nom]["exactitude"] for r in runs]
        res["systemes"][nom] = {"macro_f1": round(st.mean(m), 4), "macro_f1_ecart_type": round(st.pstdev(m), 4), "macro_f1_par_graine": m,
                                "exactitude": round(st.mean(a), 4)}
    return res


def main() -> None:
    res = synthese()
    (DOSSIER / "lora_synthese.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    for nom, v in res["systemes"].items():
        print(f'{nom:28s} {v["macro_f1"]:.3f} ± {v["macro_f1_ecart_type"]:.3f}  ({res["n_graines"]} graines)  {v["macro_f1_par_graine"]}')


if __name__ == "__main__":
    main()
