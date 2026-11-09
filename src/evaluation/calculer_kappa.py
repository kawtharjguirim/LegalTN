"""Accord inter-annotateurs entre deux fichiers annotés indépendamment.

Deux modes :
- `categorie` (défaut) : kappa de Cohen sur un champ à valeurs discrètes
  (ex. `modal` des obligations, `verdict_image` du rappel d'alignement) ;
- `spans` : accord F1 entre les entités NER des deux annotateurs (format
  `debut|fin|TYPE;...`). Le kappa n'est pas adapté aux spans : on publie
  l'accord F1 (un annotateur pris comme référence, l'autre comme prédiction).

Le script REFUSE de calculer (code de sortie 2) si :
- un fichier est absent ;
- aucune ligne n'est annotée par les DEUX annotateurs sur les mêmes identifiants.
Un champ vide n'est jamais compté comme une annotation (ni comme un désaccord).

Exemples :
  python src/evaluation/calculer_kappa.py --a data/dev/obligations_candidats_dev_v1.csv \
      --b data/dev/double_annotation/obligations_annotateur_B.csv --id obligation_id --champ modal
  python src/evaluation/calculer_kappa.py --mode spans --a data/dev/ner_a_annoter_v1.csv \
      --b data/dev/double_annotation/ner_annotateur_B.csv --id item_id --champ entites
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

EFFECTIF_CONSEILLE = 50


class RefusDeCalcul(Exception):
    """Données insuffisantes : aucun chiffre ne doit être publié."""


def lire(chemin: Path) -> list[dict]:
    if not chemin.exists():
        raise RefusDeCalcul(f"fichier absent : {chemin}")
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def paires_annotees(a: list[dict], b: list[dict], ident: str, champ: str) -> list[tuple[str, str, str]]:
    """(id, valeur A, valeur B) pour les identifiants annotés par les deux annotateurs."""
    for nom, lignes in (("A", a), ("B", b)):
        if lignes and (ident not in lignes[0] or champ not in lignes[0]):
            raise RefusDeCalcul(f"colonnes « {ident} » ou « {champ} » absentes du fichier {nom}")
    valeurs_b = {r[ident].strip(): r[champ].strip() for r in b if r.get(champ, "").strip()}
    paires = [(r[ident].strip(), r[champ].strip(), valeurs_b[r[ident].strip()])
              for r in a if r.get(champ, "").strip() and r[ident].strip() in valeurs_b]
    if not paires:
        raise RefusDeCalcul("aucune ligne annotée par les deux annotateurs : calcul refusé "
                            "(un champ vide n'est pas une annotation)")
    return paires


def kappa_cohen(paires: list[tuple[str, str, str]]) -> dict:
    n = len(paires)
    accord = sum(va == vb for _, va, vb in paires) / n
    freq_a = Counter(va for _, va, _ in paires)
    freq_b = Counter(vb for _, _, vb in paires)
    attendu = sum(freq_a[c] * freq_b[c] for c in freq_a.keys() | freq_b.keys()) / (n * n)
    kappa = None if attendu == 1 else (accord - attendu) / (1 - attendu)
    confusion = Counter(f"{va} / {vb}" for _, va, vb in paires)
    return {"n": n, "accord_observe": round(accord, 4), "accord_attendu": round(attendu, 4),
            "kappa": None if kappa is None else round(kappa, 4),
            "remarque_kappa": "indéfini : une seule catégorie utilisée par les deux annotateurs"
            if kappa is None else "",
            "confusion_A_sur_B": dict(sorted(confusion.items()))}


def lire_spans(valeur: str) -> set[tuple[int, int, str]]:
    spans = set()
    for morceau in filter(None, (m.strip() for m in valeur.split(";"))):
        debut, fin, type_ = morceau.split("|")
        spans.add((int(debut), int(fin), type_.strip()))
    return spans


def accord_spans(paires: list[tuple[str, str, str]]) -> dict:
    vp = n_a = n_b = 0
    for _, va, vb in paires:
        sa, sb = lire_spans(va), lire_spans(vb)
        vp += len(sa & sb)
        n_a += len(sa)
        n_b += len(sb)
    p = vp / n_b if n_b else 0.0
    r = vp / n_a if n_a else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"n_phrases": len(paires), "entites_A": n_a, "entites_B": n_b, "communes": vp,
            "accord_F1": round(f1, 4), "precision_B_sur_A": round(p, 4), "rappel_B_sur_A": round(r, 4)}


def calculer(chemin_a: Path, chemin_b: Path, ident: str, champ: str, mode: str = "categorie") -> dict:
    paires = paires_annotees(lire(chemin_a), lire(chemin_b), ident, champ)
    resultat = kappa_cohen(paires) if mode == "categorie" else accord_spans(paires)
    n = resultat.get("n", resultat.get("n_phrases"))
    resultat.update({"mode": mode, "champ": champ, "fichier_A": str(chemin_a), "fichier_B": str(chemin_b),
                     "avertissement": f"effectif faible (< {EFFECTIF_CONSEILLE}) : intervalle de confiance large"
                     if n < EFFECTIF_CONSEILLE else ""})
    return resultat


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--a", type=Path, required=True, help="fichier de l'annotateur A")
    parser.add_argument("--b", type=Path, required=True, help="fichier de l'annotateur B")
    parser.add_argument("--id", required=True, help="colonne identifiant commune (ex. obligation_id)")
    parser.add_argument("--champ", required=True, help="colonne annotée (ex. modal, verdict_image, entites)")
    parser.add_argument("--mode", choices=["categorie", "spans"], default="categorie")
    parser.add_argument("--sortie", type=Path, help="fichier JSON de résultat (facultatif)")
    args = parser.parse_args(argv)
    try:
        resultat = calculer(args.a, args.b, args.id, args.champ, args.mode)
    except RefusDeCalcul as e:
        print(f"CALCUL REFUSÉ : {e}", file=sys.stderr)
        return 2
    texte = json.dumps(resultat, ensure_ascii=False, indent=2)
    print(texte)
    if args.sortie:
        if args.sortie.exists():
            print(f"{args.sortie} existe déjà : non écrasé.", file=sys.stderr)
            return 1
        args.sortie.write_text(texte, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
