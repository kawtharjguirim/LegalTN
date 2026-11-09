"""Récupère de vraies réponses de l'API locale pour les maquettes (aucune donnée inventée)."""
import json, sys, urllib.request

PORT = sys.argv[1]
QUESTIONS = sys.argv[2:]
sortie = {}
for q in QUESTIONS:
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/repondre",
                                 data=json.dumps({"question": q, "k": 3}).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req))
    sortie[q] = d
    print(q, "| corr:", [(c["avant"], c["apres"]) for c in d["corrections"]],
          "| abst:", d["abstention"], "|",
          [(c["article"], c["page"], round(c["score"], 2)) for c in d["candidats"]])
json.dump(sortie, open("design/reponses.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
