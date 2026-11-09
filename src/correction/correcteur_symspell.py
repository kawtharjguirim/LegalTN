"""Correction orthographique des questions par SymSpell, sans LLM.

Principe : un mot de la question absent du vocabulaire du Code du travail est
remplacé par le mot du corpus le plus proche (distance d'édition de
Damerau-Levenshtein), et en cas d'égalité par le plus fréquent dans le corpus.

Ordre des étapes pour chaque question :
  1. lexique de sigles (CDI -> contrat à durée indéterminée…), appliqué avant SymSpell ;
  2. pour chaque mot : on ne touche pas aux nombres, aux mots de moins de 3 lettres
     ni aux mots déjà connus (vocabulaire du corpus, ou lexique général FR/AR de
     pyspellchecker : « rompre » ou « capitale » sont corrects même absents du Code) ;
  3. sinon, recherche SymSpell avec distance max 1 (mot de 4 lettres ou moins) ou 2.

Dictionnaires : construits à partir des articles de data/processed/, avec la
fréquence réelle de chaque mot. Aucun fichier de data/test_locked/ n'est lu.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path

from spellchecker import SpellChecker
from symspellpy import SymSpell, Verbosity

RACINE = Path(__file__).resolve().parents[2]
CORPUS_FR = RACINE / "data" / "processed" / "articles_fr_corrige.csv"
CORPUS_AR = RACINE / "data" / "processed" / "articles_ar.csv"

LONGUEUR_MIN = 3          # mots plus courts : jamais corrigés
SEUIL_DISTANCE_1 = 4      # longueur <= 4 : distance max 1, sinon 2
DISTANCE_MAX = 2

# Sigles courants absents du texte de loi (le Code écrit les termes en entier).
SIGLES = {
    "CDI": "contrat à durée indéterminée",
    "CDD": "contrat à durée déterminée",
    "SMIG": "salaire minimum interprofessionnel garanti",
    "SMAG": "salaire minimum agricole garanti",
    "CNSS": "caisse nationale de sécurité sociale",
}

# Mots de question et mots tunisiens translittérés : ils sont corrects mais rares ou
# absents d'un texte de loi. Sans cette liste, « combien » serait « corrigé ».
MOTS_PROTEGES_FR = set("""
quel quelle quels quelles combien comment pourquoi quand quoi est-ce puis peut peux
dois doit faut salarie salariee salaries employe employee patron boss
ken chnowa chkoun kifech win chhal mta mouch yemken lazem najem najjem
""".split())

PREFIXES_AR = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")
SUFFIXES_AR = ("هما", "كما", "ات", "ون", "ين", "ان", "ها", "هم", "هن", "كم", "نا", "ه", "ي", "ك")


def normaliser_fr(mot: str) -> str:
    """Minuscules et accents retirés : « Préavis » -> « preavis »."""
    mot = unicodedata.normalize("NFD", mot.lower())
    return "".join(c for c in mot if unicodedata.category(c) != "Mn")


def normaliser_ar(mot: str) -> str:
    """أإآ -> ا, ة -> ه, ى -> ي, sans diacritiques (tachkil) ni tatweel."""
    mot = "".join(c for c in unicodedata.normalize("NFD", mot) if unicodedata.category(c) != "Mn")
    mot = mot.replace("ـ", "")
    mot = re.sub("[إأآٱ]", "ا", mot)
    return mot.replace("ة", "ه").replace("ى", "ي")


def reduire_ar(mot: str) -> tuple[str, str, str]:
    """Retrait léger : au plus un préfixe et un suffixe, en gardant 3 lettres au moins.

    Retourne (préfixe, racine réduite, suffixe) pour pouvoir recoller la forme corrigée.
    """
    prefixe = suffixe = ""
    for p in PREFIXES_AR:
        if mot.startswith(p) and len(mot) - len(p) >= 3:
            prefixe, mot = p, mot[len(p):]
            break
    for s in SUFFIXES_AR:
        if mot.endswith(s) and len(mot) - len(s) >= 3:
            suffixe, mot = s, mot[: -len(s)]
            break
    return prefixe, mot, suffixe


def developper_sigles(texte: str, corrections: list | None = None, corriger_mot=None) -> str:
    """CDI -> contrat à durée indéterminée.

    Si le mot juste avant le sigle est déjà le premier mot du développement
    (« contrat CDI »), il n'est pas répété : « contrat à durée indéterminée ».
    `corriger_mot` sert seulement à cette comparaison (« contart CDI » est reconnu).
    """
    def remplacer(m: re.Match) -> str:
        avant, sig = m.group(1), m.group(2)
        developpe = SIGLES[sig]
        premier, _, reste = developpe.partition(" ")
        compare = (corriger_mot(avant) or avant) if (avant and corriger_mot) else avant
        insere = reste if avant and normaliser_fr(compare) == normaliser_fr(premier) else developpe
        if corrections is not None:
            corrections.append({"type": "sigle", "avant": sig, "apres": insere})
        return (avant + " " if avant else "") + insere

    motif = r"(?:\b([^\W\d_]+)\s+)?\b(" + "|".join(SIGLES) + r")\b"
    return re.sub(motif, remplacer, texte)


def est_arabizi(question: str) -> bool:
    """Vrai si un mot mélange lettres latines et chiffres (« mta3 », « ch7al », « 9anoun »)."""
    return bool(re.search(r"\b(?=\w*[a-zA-Z])(?=\w*\d)\w+\b", question))


def distance_max(mot: str) -> int:
    return 1 if len(mot) <= SEUIL_DISTANCE_1 else DISTANCE_MAX


def _lire_textes(chemin: Path, colonne: str) -> list[str]:
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return [r[colonne] for r in csv.DictReader(f)]


def _symspell(frequences: Counter) -> SymSpell:
    sym = SymSpell(max_dictionary_edit_distance=DISTANCE_MAX, prefix_length=7)
    for mot, n in frequences.items():
        sym.create_dictionary_entry(mot, n)
    return sym


def _lexique_general(langue: str) -> set[str]:
    """Mots connus de la langue (sert uniquement à NE PAS corriger, jamais à proposer)."""
    return set(SpellChecker(language=langue).word_frequency.dictionary)


class Correcteur:
    def __init__(self, textes_fr: list[str] | None = None, textes_ar: list[str] | None = None,
                 lexique_general: bool = True, mots_vides: dict[str, set[str]] | None = None):
        self.lexique_fr = _lexique_general("fr") if lexique_general else set()
        self.lexique_fr |= {normaliser_fr(w) for w in self.lexique_fr}
        self.lexique_ar = _lexique_general("ar") if lexique_general else set()
        # Mots vides : ni comptés dans les dictionnaires, ni proposés comme correction.
        vides_fr = {normaliser_fr(w) for w in (mots_vides or {}).get("fr", ())}
        vides_ar = {normaliser_ar(w) for w in (mots_vides or {}).get("ar", ())}
        textes_fr = _lire_textes(CORPUS_FR, "texte_fr") if textes_fr is None else textes_fr
        textes_ar = _lire_textes(CORPUS_AR, "texte_ar") if textes_ar is None else textes_ar

        # FR : fréquence de chaque mot normalisé + forme accentuée la plus fréquente,
        # pour proposer « préavis » et non « preavis » à l'utilisateur.
        self.freq_fr: Counter = Counter()
        formes: dict[str, Counter] = {}
        for texte in textes_fr:
            for mot in re.findall(r"[^\W\d_]+", texte.lower()):
                cle = normaliser_fr(mot)
                if cle in vides_fr:
                    continue
                self.freq_fr[cle] += 1
                formes.setdefault(cle, Counter())[mot] += 1
        self.forme_fr = {cle: c.most_common(1)[0][0] for cle, c in formes.items()}
        self.sym_fr = _symspell(self.freq_fr)

        # AR : fréquences des formes complètes et des formes réduites (sans préfixe/suffixe).
        self.freq_ar: Counter = Counter()
        self.freq_ar_reduit: Counter = Counter()
        for texte in textes_ar:
            for mot in re.findall(r"[^\W\d_]+", normaliser_ar(texte)):
                if mot in vides_ar:
                    continue
                self.freq_ar[mot] += 1
                self.freq_ar_reduit[reduire_ar(mot)[1]] += 1
        self.sym_ar = _symspell(self.freq_ar_reduit)

    # --- décisions mot par mot -------------------------------------------------

    def _corriger_fr(self, mot: str) -> str | None:
        cle = normaliser_fr(mot)
        if cle in self.freq_fr or cle in MOTS_PROTEGES_FR or mot.lower() in self.lexique_fr:
            return None
        suggestions = self.sym_fr.lookup(cle, Verbosity.CLOSEST, max_edit_distance=distance_max(cle))
        if not suggestions:
            return None
        return self.forme_fr[suggestions[0].term]

    def _corriger_ar(self, mot: str) -> str | None:
        norm = normaliser_ar(mot)
        prefixe, reduit, suffixe = reduire_ar(norm)
        # Correct s'il existe en forme complète ou réduite.
        if (norm in self.freq_ar or reduit in self.freq_ar_reduit
                or mot in self.lexique_ar or norm in self.lexique_ar):
            return None
        if len(reduit) < LONGUEUR_MIN:
            return None
        suggestions = self.sym_ar.lookup(reduit, Verbosity.CLOSEST, max_edit_distance=distance_max(reduit))
        if not suggestions:
            return None
        return prefixe + suggestions[0].term + suffixe

    def est_mot_francais(self, mot: str) -> bool:
        """Mot connu du Code ou du lexique général français (sert à la translittération)."""
        cle = normaliser_fr(mot)
        return cle in self.freq_fr or cle in self.lexique_fr or mot.lower() in self.lexique_fr

    def corriger_jeton(self, jeton: str, langue: str, deja_reduit: bool = False) -> str | None:
        """Version pipeline : jeton déjà normalisé (et déjà racinisé en arabe si deja_reduit)."""
        if any(c.isdigit() for c in jeton) or len(jeton) < LONGUEUR_MIN:
            return None
        if langue != "ar" or not deja_reduit:
            return self.corriger_mot(jeton, langue)
        if jeton in self.freq_ar_reduit or jeton in self.freq_ar or jeton in self.lexique_ar:
            return None
        s = self.sym_ar.lookup(jeton, Verbosity.CLOSEST, max_edit_distance=distance_max(jeton))
        return s[0].term if s else None

    def corriger_mot(self, mot: str, langue: str) -> str | None:
        """Retourne la correction, ou None si le mot doit rester tel quel."""
        if any(c.isdigit() for c in mot) or len(mot) < LONGUEUR_MIN:
            return None
        return self._corriger_ar(mot) if langue == "ar" else self._corriger_fr(mot)

    # --- question complète -----------------------------------------------------

    def corriger(self, question: str, langue: str = "fr") -> dict:
        corrections = []

        texte = developper_sigles(question, corrections, lambda w: self.corriger_mot(w, langue))

        # Arabizi tunisien (« mta3 », « wa7ed ») : pas de dictionnaire fiable, on ne corrige pas
        # l'orthographe (sinon « fel » deviendrait « tel »). Les sigles restent développés.
        if langue == "fr" and est_arabizi(question):
            return {"question_originale": question, "question_corrigee": texte, "corrections": corrections}

        def mot(m: re.Match) -> str:
            original = m.group(0)
            # Majuscule hors début de phrase = nom propre ou sigle inconnu (Sousse, SONEDE) : intact.
            if original[:1].isupper() and m.start() > 0 and texte[:m.start()].strip():
                return original
            propose = self.corriger_mot(original, langue)
            if propose is None or normaliser_fr(propose) == normaliser_fr(original):
                return original
            if original[:1].isupper():
                propose = propose[:1].upper() + propose[1:]
            corrections.append({"type": "orthographe", "avant": original, "apres": propose})
            return propose

        # Mots = suites de lettres ou de chiffres ; « l'article » donne « l » et « article ».
        texte = re.sub(r"[^\W_]+", mot, texte)
        return {"question_originale": question, "question_corrigee": texte, "corrections": corrections}


_INSTANCE: Correcteur | None = None


def correcteur() -> Correcteur:
    """Instance partagée : les dictionnaires ne sont construits qu'une fois."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Correcteur()
    return _INSTANCE
