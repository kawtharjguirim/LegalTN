import numpy as np

from src.platinum.calibration import aire_risque, auroc, base, risque_couverture


def test_base_numero_article():
    assert base("63-2") == "63" and base("376 bis") == "376" and base("FR-95") == "95" and base("261") == "261"


def test_auroc_parfait_et_hasard():
    s = np.array([0.9, 0.8, 0.3, 0.2])
    assert auroc(s, np.array([True, True, False, False])) == 1.0
    assert auroc(s, np.array([True, False, True, False])) == 0.75
    assert auroc(np.array([0.5, 0.5]), np.array([True, False])) == 0.5


def test_risque_couverture_monotone_sur_signal_parfait():
    scores = np.array([0.9, 0.8, 0.7, 0.2, 0.1])
    correct = np.array([True, True, True, False, False])
    pts = risque_couverture(scores, correct)
    assert [p["risque"] for p in pts] == [0.0, 0.0, 0.0, 0.25, 0.4]
    assert aire_risque(pts) < aire_risque(risque_couverture(scores, correct[::-1]))
