"""Analyse de l'étude d'utilité (plan croisé, comparaison appariée LegalTN − Code seul).

Entrées (dossier ``etude_utilite/resultats/``) : ``*_taches.csv`` exportés par ``outils/etude_utilite.html``
dont les colonnes ``note_reponse`` et ``note_article`` ont été remplies par le notateur (0/1), et
``*_questionnaires.csv``. Le corrigé et le périmètre viennent de ``etude_utilite/taches_v1.csv``.

Sorties : ``reports/platinum/etude_utilite/resultats.json`` et ``RESULTATS.md``.
Refuse de calculer si des notes manquent (une réponse non notée n'est pas une erreur).

Usage : python -X utf8 -m src.etude.analyser [--resultats etude_utilite/resultats]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics as st
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CONDITIONS = ("LegalTN", "Code")


def lire(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def moyenne(v: list[float]) -> float | None:
    return sum(v) / len(v) if v else None


def metriques(taches: list[dict], perimetre: dict[str, bool]) -> dict[str, float | None]:
    """Métriques d'un participant dans une condition (une série de 6 questions)."""
    dans = [t for t in taches if perimetre[t["tache_id"]]]
    hors = [t for t in taches if not perimetre[t["tache_id"]]]
    fausses = [float(t["confiance"]) for t in dans if int(t["note_reponse"]) == 0]
    return {
        "exactitude": moyenne([int(t["note_reponse"]) for t in dans]),
        "citation": moyenne([int(t["note_article"]) for t in dans]),
        "abstention": moyenne([int(t["note_reponse"]) for t in hors]),
        "temps_median_s": st.median([float(t["duree_s"]) for t in taches]) if taches else None,
        "confiance": moyenne([float(t["confiance"]) for t in taches]),
        "confiance_sur_fausses": moyenne(fausses),
    }


def bootstrap_ic(diffs: list[float], n: int = 10000, graine: int = 20261121) -> tuple[float, float]:
    rng = random.Random(graine)
    moy = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return moy[int(0.025 * n)], moy[int(0.975 * n) - 1]


def permutation_p(diffs: list[float], n_max: int = 20000, graine: int = 20261121) -> float:
    """Test de permutation par inversion de signes (exact si 2^n <= n_max, sinon Monte-Carlo)."""
    obs = abs(sum(diffs))
    n = len(diffs)
    if 2 ** n <= n_max:
        tot = sum(1 for m in range(2 ** n)
                  if abs(sum(d if (m >> i) & 1 else -d for i, d in enumerate(diffs))) >= obs - 1e-12)
        return tot / 2 ** n
    rng = random.Random(graine)
    tot = sum(1 for _ in range(n_max) if abs(sum(d * rng.choice((-1, 1)) for d in diffs)) >= obs - 1e-12)
    return (tot + 1) / (n_max + 1)


def comparer(par_participant: dict[str, dict[str, dict]], cle: str) -> dict:
    """Différence appariée LegalTN − Code sur les participants ayant la valeur dans les deux conditions."""
    paires = [(v["LegalTN"][cle], v["Code"][cle]) for v in par_participant.values()
              if v.get("LegalTN", {}).get(cle) is not None and v.get("Code", {}).get(cle) is not None]
    out = {"n_apparies": len(paires)}
    if len(paires) < 2:
        return out | {"remarque": "moins de 2 participants appariés : pas de comparaison"}
    diffs = [a - b for a, b in paires]
    lo, hi = bootstrap_ic(diffs)
    out |= {"legaltn": round(moyenne([a for a, _ in paires]), 3), "code": round(moyenne([b for _, b in paires]), 3),
            "difference": round(moyenne(diffs), 3), "ic95": [round(lo, 3), round(hi, 3)],
            "p_permutation": round(permutation_p(diffs), 4)}
    return out


def sus(questionnaires: list[dict]) -> dict:
    par = {}
    for q in questionnaires:
        par.setdefault(q["participant"], {})[q["condition"]] = {"sus": float(q["sus_score"])}
    return comparer(par, "sus")


def analyser(dossier: Path, taches_ref: Path) -> dict:
    perimetre = {t["id"]: t["dans_perimetre"].strip() == "oui" for t in lire(taches_ref)}
    taches = [t for f in sorted(dossier.glob("*_taches.csv")) for t in lire(f)]
    questionnaires = [q for f in sorted(dossier.glob("*_questionnaires.csv")) for q in lire(f)]
    if not taches:
        raise SystemExit(f"Aucun fichier *_taches.csv dans {dossier} : pas de passation, rien à analyser.")
    manquantes = [t["tache_id"] + "/" + t["participant"] for t in taches if t["note_reponse"].strip() == "" or t["note_article"].strip() == ""]
    if manquantes:
        raise SystemExit(f"{len(manquantes)} réponses non notées (note_reponse / note_article) : {manquantes[:5]}…")
    par: dict[str, dict[str, dict]] = {}
    groupes: dict[str, list[dict]] = {}
    for t in taches:
        groupes.setdefault((t["participant"], t["condition"]), []).append(t)
    for (p, c), lst in groupes.items():
        par.setdefault(p, {})[c] = metriques(lst, perimetre)
    res = {"n_participants": len(par),
           "par_groupe": {g: sum(1 for t in taches if t["groupe"] == g and t["tache_id"] == "E01" or
                                 t["groupe"] == g and t["tache_id"] == "E07") for g in ("G1", "G2", "G3", "G4")},
           "comparaisons": {k: comparer(par, k) for k in ("exactitude", "citation", "abstention", "temps_median_s",
                                                         "confiance", "confiance_sur_fausses")},
           "sus": sus(questionnaires) if questionnaires else None}
    prefs = [q["preference"] for q in questionnaires if q.get("preference")]
    res["preferences"] = {v: prefs.count(v) for v in sorted(set(prefs))}
    return res


def markdown(res: dict) -> str:
    noms = {"exactitude": "Exactitude (questions dans le Code)", "citation": "Bon article cité",
            "abstention": "Absence de réponse reconnue (hors Code)", "temps_median_s": "Temps médian par question (s)",
            "confiance": "Confiance moyenne (1–5)", "confiance_sur_fausses": "Confiance sur les réponses fausses (1–5)"}
    lignes = [f"# Étude d'utilité — résultats ({res['n_participants']} participants)", "",
              "| Mesure | n appariés | LegalTN | Code seul | Différence | IC 95 % | p (permutation) |", "|---|---:|---:|---:|---:|---|---:|"]
    for k, nom in noms.items():
        c = res["comparaisons"][k]
        if "difference" in c:
            lignes.append(f"| {nom} | {c['n_apparies']} | {c['legaltn']} | {c['code']} | {c['difference']:+} | [{c['ic95'][0]}, {c['ic95'][1]}] | {c['p_permutation']} |")
        else:
            lignes.append(f"| {nom} | {c['n_apparies']} | – | – | – | – | – |")
    s = res.get("sus")
    if s and "difference" in s:
        lignes.append(f"| SUS (0–100) | {s['n_apparies']} | {s['legaltn']} | {s['code']} | {s['difference']:+} | [{s['ic95'][0]}, {s['ic95'][1]}] | {s['p_permutation']} |")
    lignes += ["", f"Préférences : {res['preferences']}", "",
               "Lecture : l'intervalle de confiance prime sur le p ; avec peu de participants il reste large."]
    return "\n".join(lignes) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resultats", type=Path, default=RACINE / "etude_utilite/resultats")
    parser.add_argument("--taches", type=Path, default=RACINE / "etude_utilite/taches_v1.csv")
    parser.add_argument("--sortie", type=Path, default=RACINE / "reports/platinum/etude_utilite")
    args = parser.parse_args()
    res = analyser(args.resultats, args.taches)
    args.sortie.mkdir(parents=True, exist_ok=True)
    (args.sortie / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.sortie / "RESULTATS.md").write_text(markdown(res), encoding="utf-8")
    print(markdown(res))


if __name__ == "__main__":
    main()
