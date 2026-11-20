"""Démo NER : annote une phrase avec un modèle fine-tuné sauvegardé, à côté des règles.

Usage :
  python -X utf8 -m src.ner_juridique.predire "L'employeur doit informer l'inspection du travail dans un délai de quinze jours."
  python -X utf8 -m src.ner_juridique.predire "يجب على المؤجر إعلام تفقدية الشغل في أجل خمسة عشر يوما."

Modèles attendus dans ``models/ner/<langue>_<modèle>`` (créés par
``entrainer --sauver models/ner``) : xlmr pour le français, arabert pour l'arabe.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from .entrainer import predire_encodeur
from .regles import annoter, lisible

RACINE = Path(__file__).resolve().parents[2]
MODELES = {"fr": "fr_xlmr", "ar": "ar_arabert"}


def main() -> None:
    phrase = " ".join(sys.argv[1:]).strip()
    if not phrase:
        print(__doc__)
        return
    langue = "ar" if any("؀" <= c <= "ۿ" for c in phrase) else "fr"
    dossier = RACINE / "models/ner" / MODELES[langue]
    print(f"Langue : {langue}")
    print(f"Règles        : {lisible(phrase, annoter(phrase, langue))}")
    if not dossier.exists():
        print(f"Modèle absent : {dossier} (lancer entrainer --sauver models/ner)")
        return
    import torch
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(dossier)
    modele = AutoModelForTokenClassification.from_pretrained(dossier)
    if torch.cuda.is_available():
        modele = modele.to("cuda")
    debut = time.perf_counter()
    spans = predire_encodeur(modele, tok, [{"phrase": phrase}])[0]
    print(f"{MODELES[langue]:13s} : {lisible(phrase, spans)}  ({(time.perf_counter() - debut) * 1000:.0f} ms)")


if __name__ == "__main__":
    main()
