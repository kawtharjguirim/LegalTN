import pytest

from src.rapports import generer_capsule_platinum as cp


def test_format_francais_et_resultat_manquant(monkeypatch, tmp_path):
    assert cp.f(0.5) == "0,500" and cp.f(0.9166, 2) == "0,92"
    monkeypatch.setattr(cp, "R", tmp_path)
    with pytest.raises(SystemExit, match="Résultat manquant"):
        cp.lire("platinum/domaine/lora_synthese.json")


def test_les_resultats_lus_par_la_video_existent():
    # Si l'un de ces fichiers manque, la vidéo ne peut pas être générée (chiffres lus, jamais saisis).
    for chemin in ("gold/audit/audit_resultats.json", "platinum/abstention/calibration.json", "platinum/domaine/resultats.json",
                   "gold/tunisien/tunisien_resultats.json", "gold/juge/accord_qwen2.5_7b.json", "platinum/references/resume.json",
                   "platinum/obligations/evaluation_dev_extracteur.json"):
        assert (cp.R / chemin).exists(), chemin
