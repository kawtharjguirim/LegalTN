"""Figures du rapport (SVG, sans dépendance) : lues dans ``reports/``, écrites dans ``reports/platinum/figures/``.

Figures : courbe risque-couverture de l'abstention, robustesse aux perturbations, macro-F1 de la classification de
domaine, R@5 des méthodes pour le tunisien. Aucun chiffre n'est saisi à la main.

Usage : python -X utf8 -m src.rapports.figures
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
R = RACINE / "reports"
SORTIE = R / "platinum/figures"
STYLE = ("<style>text{font-family:Segoe UI,Arial,sans-serif;font-size:12px;fill:#344054}.t{font-size:14px;font-weight:600}"
         ".g{stroke:#E4E1D8}.b{fill:#2F6FB3}.r{fill:#667085}.v{fill:#2E7D5B}.m{fill:#B4412F}</style>")


def e(t) -> str:
    return html.escape(str(t))


def barres(titre: str, items: list[tuple[str, float, str]], maxi: float = 1.0, largeur: int = 640, note: str = "") -> str:
    """Barres horizontales : items = (libellé, valeur, classe CSS)."""
    h = 54 + 26 * len(items) + (18 if note else 0)
    x0, w = 250, largeur - 250 - 60
    corps = f'<text x="10" y="22" class="t">{e(titre)}</text>'
    for i, (lib, v, cls) in enumerate(items):
        y = 44 + 26 * i
        corps += (f'<text x="{x0 - 8}" y="{y + 12}" text-anchor="end">{e(lib)}</text>'
                  f'<rect x="{x0}" y="{y}" width="{max(0.0, v / maxi) * w:.1f}" height="16" class="{cls}"/>'
                  f'<text x="{x0 + max(0.0, v / maxi) * w + 6:.1f}" y="{y + 12}">' + f"{v:.3f}".replace(".", ",") + "</text>")
    if note:
        corps += f'<text x="10" y="{h - 6}" style="font-size:11px">{e(note)}</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur} {h}" width="{largeur}">{STYLE}<rect width="100%" height="100%" fill="#FBFBF8"/>{corps}</svg>'


def courbe_risque() -> str | None:
    pts = [x for x in csv.DictReader(open(R / "platinum/abstention/points.csv", encoding="utf-8-sig")) if x["jeu"] == "dev"] \
        if (R / "platinum/abstention/points.csv").exists() else []
    if not pts:
        return None
    ordre = sorted(pts, key=lambda x: -float(x["cosnorm"]))
    ok, xs, ys = 0, [], []
    for i, x in enumerate(ordre, 1):
        ok += x["dans"] == "True" and x["bon_top1"] == "True"
        xs.append(i / len(ordre))
        ys.append(1 - ok / i)
    L, H, m = 560, 330, 56
    px, py = (lambda v: m + v * (L - m - 20)), (lambda v: H - 46 - v * (H - 46 - 40))
    g = "".join(f'<line x1="{px(0)}" x2="{px(1)}" y1="{py(t)}" y2="{py(t)}" class="g"/><text x="{m - 8}" y="{py(t) + 4}" text-anchor="end">{int(t * 100)} %</text>'
                f'<text x="{px(t)}" y="{H - 28}" text-anchor="middle">{int(t * 100)} %</text>' for t in (0, 0.25, 0.5, 0.75, 1))
    ligne = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}">{STYLE}<rect width="100%" height="100%" fill="#FBFBF8"/>'
            f'<text x="10" y="22" class="t">Courbe risque-couverture de l\'abstention (dev, 77 questions)</text>{g}'
            f'<polyline points="{ligne}" fill="none" stroke="#2F6FB3" stroke-width="2.5"/>'
            f'<text x="{px(0.5)}" y="{H - 8}" text-anchor="middle">couverture : part des questions auxquelles le système répond</text>'
            f'<text x="14" y="{py(0.5)}" transform="rotate(-90 14 {py(0.5)})" text-anchor="middle">risque d\'erreur</text></svg>')


def main() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    sorties = {}
    c = courbe_risque()
    if c:
        sorties["risque_couverture.svg"] = c
    a = json.loads((R / "gold/audit/audit_resultats.json").read_text(encoding="utf-8")) if (R / "gold/audit/audit_resultats.json").exists() else None
    if a:
        items = [(k.replace(" (original répété)", "").replace("_", " "), v["decision"], "r" if k.startswith("bruit") else "b") for k, v in a["invariance"].items()]
        sorties["robustesse.svg"] = barres("Robustesse : décision identique à celle de la question d'origine", items,
                                           note="Barre grise : bruit du LLM seul (même question reposée).")
    d = json.loads((R / "platinum/domaine/resultats.json").read_text(encoding="utf-8")) if (R / "platinum/domaine/resultats.json").exists() else None
    if d:
        noms = {"majorite_fr": "Majorité", "tfidf_fr": "TF-IDF (FR)", "tfidf_ar": "TF-IDF (AR)", "e5_fr": "e5 + LR (FR)", "e5_ar": "e5 + LR (AR)",
                "transfert_fr_vers_ar": "Transfert FR → AR", "transfert_ar_vers_fr": "Transfert AR → FR"}
        items = [(noms[k], v["macro_f1"], "r" if k.startswith("majorite") else "b") for k, v in d["systemes"].items() if k in noms]
        src_lora = R / "platinum/domaine/lora_synthese.json" if (R / "platinum/domaine/lora_synthese.json").exists() else R / "platinum/domaine/lora.json"
        synth = json.loads(src_lora.read_text(encoding="utf-8")) if src_lora.exists() else {}
        lora = synth.get("systemes", {})
        etiq = {"lora_fr": "LoRA (FR)", "lora_ar": "LoRA (AR)", "lora_transfert_fr_vers_ar": "LoRA FR → AR", "lora_transfert_ar_vers_fr": "LoRA AR → FR"}
        items += [(etiq[k], v["macro_f1"], "v") for k, v in lora.items() if k in etiq]
        sorties["domaine.svg"] = barres("Classification de domaine : macro-F1 (12 domaines)", items, note=f"Validation croisée par blocs ; LoRA : moyenne de {synth.get('n_graines', 1)} graine(s).")
    t = json.loads((R / "gold/tunisien/tunisien_resultats.json").read_text(encoding="utf-8")) if (R / "gold/tunisien/tunisien_resultats.json").exists() else None
    if t:
        noms = {"directe_fr": "Recherche directe", "multilingue": "Multilingue direct", "translit_ar": "Translittération", "traduction_fr": "Traduction FR (3B)", "traduction_ar": "Traduction AR (3B)"}
        items = [(noms[k], v["global"]["r_at_5"], "b") for k, v in t["methodes"].items() if k in noms]
        p7 = R / "gold/tunisien/qwen7b/tunisien_resultats.json"
        if p7.exists():
            v = json.loads(p7.read_text(encoding="utf-8"))["methodes"].get("traduction_fr")
            if v:
                items.append(("Traduction FR (7B)", v["global"]["r_at_5"], "v"))
        sorties["tunisien.svg"] = barres("Questions en tunisien : R@5 par méthode", items, note="30 questions dans le Code.")
    for nom, svg in sorties.items():
        (SORTIE / nom).write_text(svg, encoding="utf-8")
        print("->", SORTIE / nom)


if __name__ == "__main__":
    main()
