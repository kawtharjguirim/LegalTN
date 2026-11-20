"""Tests de l'extraction des nombres (chiffres et lettres, FR et AR)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.divergences.nombres import nombres_ar, nombres_fr


def test_francais():
    assert nombres_fr("dans un délai de quinze jours") == {1, 15}
    assert nombres_fr("quatre vingt dix jours de salaire") == {90}
    assert nombres_fr("une amende de 120 à 300 dinars") == {1, 120, 300}
    assert nombres_fr("dix-huit ans") == {18}


def test_arabe():
    assert nombres_ar("في أجل خمسة عشر يوما") == {15}
    assert nombres_ar("ثمان وأربعين ساعة") == {48}
    assert nombres_ar("لا يكون دون شهرين") == {2}
    assert nombres_ar("خطية من 120 إلى 300 دينار") == {120, 300}
    assert nombres_ar("دون الثامنة عشرة") == {18}
    assert nombres_ar("خمسة آلاف دينار") == {5000}
    assert nombres_ar("مائة دينار") == {100}
