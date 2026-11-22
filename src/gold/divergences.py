"""Gold - detection automatique de divergences AR / FR entre versions d'un meme article.

Signaux independants, chacun explicable (aucun apprentissage, aucun reglage sur les annotations) :
- nombres : ensembles de nombres differents (hors numero de l'article et hors annees de modification) ;
- references : articles cites differents (« article 12 » vs « الفصل 12 ») ;
- modalite : obligation / interdiction / permission presente dans une langue et absente de l'autre ;
- negation : nombre de negations tres different ;
- longueur : rapport de longueur atypique (|z| > 2 sur le log du rapport).
Sortie : un CSV a faire verifier par l'equipe (colonnes verdict_humain et commentaire vides).
"""
import argparse
import csv
import math
import re
import statistics
from pathlib import Path

NOMBRE = re.compile(r"\d+")
REF_FR = re.compile(r"\barticles?\s+(\d+)", re.IGNORECASE)
REF_AR = re.compile(r"الفص(?:ل|ول)\s+(\d+)")
MODIF_FR = re.compile(r"\((?:[^()]*(?:modifi|ajout|abrog)[^()]*)\)", re.IGNORECASE)
MODIF_AR = re.compile(r"\((?:[^()]*(?:نقح|أضيف|ألغي|اضيف|الغي)[^()]*)\)")
MODAUX = {
    "obligation": (r"\bdoi(?:t|vent)\b|\btenu[es]?\b|\bobligatoire|\best tenu", r"يجب|يتعين|يتعيّن|ملزم|وجوبا"),
    "interdiction": (r"\binterdit|\bne (?:peut|peuvent) |\bil est interdit", r"يحجر|يمنع|لا يجوز|لا يمكن"),
    "permission": (r"\bpeu(?:t|vent)\b|\bpossibilit|\ba le droit|\bont le droit", r"يمكن|يجوز|يحق|له الحق"),
}
NEG_FR = re.compile(r"\bne\b|\bn'|\bn’|\bsans\b|\baucun", re.IGNORECASE)
NEG_AR = re.compile(r"(?:^|\s)(?:لا|لم|لن|ليس|غير|دون)(?:\s|$)")


def corps(texte, modif):
    """Retire l'en-tete (« Article 4.- », « الفصل 6 (...).- ») et les mentions de modification."""
    t = modif.sub(" ", texte)
    return re.sub(r"^\s*(?:Article|الفصل)\s*\d+\s*(?:bis|ter|quater|مكرر)?\s*[.\-–]*", " ", t)


def analyser(fr, ar):
    cf, ca = corps(fr, MODIF_FR), corps(ar, MODIF_AR)
    nf, na = set(NOMBRE.findall(cf)), set(NOMBRE.findall(ca))
    rf, ra = set(REF_FR.findall(cf)), set(REF_AR.findall(ca))
    sig = {}
    if nf != na:
        sig["nombres"] = f"FR seulement {sorted(nf - na)} ; AR seulement {sorted(na - nf)}"
    if rf != ra:
        sig["references"] = f"FR {sorted(rf)} ; AR {sorted(ra)}"
    for nom, (mf, ma) in MODAUX.items():
        a, b = bool(re.search(mf, cf, re.IGNORECASE)), bool(re.search(ma, ca))
        if a != b:
            sig["modal_" + nom] = "FR" if a else "AR"
    gf, ga = len(NEG_FR.findall(cf)), len(NEG_AR.findall(ca))
    if abs(gf - ga) >= 2:
        sig["negation"] = f"FR {gf} ; AR {ga}"
    return sig, math.log((len(cf) + 1) / (len(ca) + 1))


def main():
    import sys
    sys.path[:0] = ["src", "src/demo"]
    import repondre
    p = argparse.ArgumentParser()
    p.add_argument("--sortie", default="reports/gold/divergences/divergences_a_verifier.csv")
    a = p.parse_args()
    c = repondre.charger()
    fr = {x["article"]: x for x in c["fr"].articles}
    ar = {x["article"]: x for x in c["ar"].articles}
    communs = sorted(set(fr) & set(ar), key=lambda k: (int(re.match(r"\d+", k).group()), k))
    lignes = []
    for k in communs:
        sig, lr = analyser(fr[k]["texte"], ar[k]["texte"])
        lignes.append((k, sig, lr))
    mu, sd = statistics.mean(l[2] for l in lignes), statistics.pstdev(l[2] for l in lignes)
    out = Path(a.sortie)
    out.parent.mkdir(parents=True, exist_ok=True)
    n_signal = 0
    compte = {}
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["article", "page_fr", "page_ar", "signaux", "detail", "divergence_predite",
                    "verdict_humain", "type_divergence", "commentaire"])
        for k, sig, lr in lignes:
            z = (lr - mu) / sd if sd else 0
            if abs(z) > 2:
                sig["longueur"] = f"z = {z:.1f}"
            for s in sig:
                compte[s.split("_")[0] if s.startswith("modal") else s] = compte.get(s, 0) + 1
            n_signal += bool(sig)
            w.writerow([k, fr[k]["page"], ar[k]["page"], ",".join(sig), " | ".join(f"{a}: {b}" for a, b in sig.items()),
                        "oui" if sig else "non", "", "", ""])
    print({"articles_communs": len(lignes), "articles_signales": n_signal, "par_signal": compte, "sortie": str(out)})


if __name__ == "__main__":
    main()
