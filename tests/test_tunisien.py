"""Tests de la détection et de la translittération de l'arabizi tunisien."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.tunisien.arabizi import est_tunisien, translitterer

RACINE = Path(__file__).resolve().parents[1]


def lire(chemin):
    with open(RACINE / chemin, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_detection_sur_les_jeux_de_dev():
    dev = lire("data/dev/questions_dev_v2.csv")
    assert all(est_tunisien(q["question"]) for q in dev if q["langue"] == "tun")
    assert not any(est_tunisien(q["question"]) for q in dev if q["langue"] == "fr")
    assert not any(est_tunisien(q["question"]) for q in dev if q["langue"] == "ar")
    tun = lire("data/dev/questions_tun_v1.csv")
    assert all(est_tunisien(q["question"]) for q in tun)


def test_translitteration():
    assert translitterer("3andi 7a9 ?") == "عندي حق؟"
    assert translitterer("el khedma") == "الخدمة"
    assert translitterer("chnowa fel jem3a") == "شنوة في الجمعة"
    assert translitterer("congé mta3 5 ayem") == "كونق متع 5 ايم"
