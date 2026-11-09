"""Pipeline de traitement des questions LegalTN, sans LLM ni modèle neuronal.

Ordre (une étape = une fonction testable) :
  1. detecter_langue           fr | ar | tunisien (arabe) | arabizi
  2. translitterer_arabizi     chiffres et lettres latines -> arabe ; mots français connus gardés
  3. retirer_mots_vides        listes data/lexiques/*.txt ; AVANT la normalisation de ى
  4. normaliser                FR : minuscules, accents ; AR : أإآ→ا, ة→ه, ى→ي, diacritiques, tatweel
  5. appliquer_lexiques        tunisien -> standard (data/dev/lexique_tunisien_v1.csv) et sigles
  6. raciniser_ar              préfixe/suffixe retirés, reste >= 3 lettres
  7. corriger_jetons           SymSpell (src/correction), mots vides exclus
  8. ajouter_synonymes         expansion (data/dev/synonymes_juridiques_v1.csv)
  9. BM25                      sur un index du corpus passé par les étapes 3, 4 et 6

Les étapes 3, 4 et 6 sont appliquées AUSSI au corpus : la question et les articles
doivent être découpés de la même façon, sinon un mot racinisé ne retrouve plus l'article.
Les étapes 5, 7 et 8 ne concernent que la question (elles la rapprochent du vocabulaire du Code).
"""
from __future__ import annotations

import csv
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RACINE), str(RACINE / "src" / "evaluation"), str(RACINE / "src" / "demo")]

from baseline_bm25 import AR, B, FR, K1, Bm25, intitule_ar, intitule_fr, lire  # noqa: E402
from src.correction.correcteur_symspell import (  # noqa: E402
    SIGLES, Correcteur, est_arabizi, normaliser_ar, normaliser_fr, reduire_ar,
)

LEXIQUES = RACINE / "data" / "lexiques"
LEXIQUE_TUNISIEN = RACINE / "data" / "dev" / "lexique_tunisien_v1.csv"
SYNONYMES = RACINE / "data" / "dev" / "synonymes_juridiques_v1.csv"
SEUIL_SCORE_MIN = 9.085   # seuil historique, inchangé (décision de l'équipe)

# Jamais retirés, même s'ils figurent par erreur dans une liste de mots vides :
# ils changent le sens juridique (« peut » / « ne peut pas », « يجوز » / « لا يجوز »).
PROTEGES_FR = {"ne", "pas", "sans", "sauf", "aucun", "aucune", "doit", "doivent",
               "peut", "peuvent", "interdit", "interdite", "obligatoire"}
PROTEGES_AR = {"لا", "ليس", "غير", "إلا", "الا", "لم", "لن", "يجب", "يمنع", "يجوز"}

# Marqueurs du dialecte tunisien (écriture arabe ou latine), déjà normalisés.
MARQUEURS_TUN_AR = {"شنوه", "شنيه", "شكون", "كيفاش", "وقتاش", "علاش", "قداش", "برشا", "باش",
                    "متاع", "موش", "ماهوش", "توا", "فما", "نجم", "نحب", "ياسر"}
MARQUEURS_ARABIZI = {"chnowa", "chnoua", "chkoun", "kifech", "kifach", "wa9tech", "3lech",
                     "9adech", "barcha", "bech", "mta3", "mouch", "taw", "fama", "ken", "wela",
                     "lezem", "lazem", "yemken", "fel", "fil", "mel"}

# Arabizi -> arabe : digrammes d'abord, puis chiffres et lettres.
DIGRAMMES = {"ch": "ش", "sh": "ش", "kh": "خ", "gh": "غ", "th": "ث", "dh": "ذ", "ou": "و"}
LETTRES = {"2": "ء", "3": "ع", "5": "خ", "7": "ح", "8": "غ", "9": "ق",
           "a": "ا", "b": "ب", "t": "ت", "j": "ج", "d": "د", "r": "ر", "z": "ز", "s": "س",
           "f": "ف", "k": "ك", "q": "ق", "g": "ق", "l": "ل", "m": "م", "n": "ن", "h": "ه",
           "w": "و", "y": "ي", "i": "ي", "o": "و", "u": "و", "p": "ب", "v": "ف", "x": "كس",
           "c": "ك", "e": ""}


def _lire_liste(chemin: Path) -> list[str]:
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lignes if l.strip() and not l.lstrip().startswith("#")]


def _sans_diacritiques(mot: str) -> str:
    """Diacritiques et tatweel seulement : ى, ة et les hamzas restent distincts."""
    mot = "".join(c for c in unicodedata.normalize("NFD", mot) if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", mot).replace("ـ", "")


def charger_mots_vides() -> dict[str, set[str]]:
    fr = {w.lower() for w in _lire_liste(LEXIQUES / "stopwords_fr.txt")} - PROTEGES_FR
    ar = {_sans_diacritiques(w) for w in _lire_liste(LEXIQUES / "stopwords_ar.txt")} - PROTEGES_AR
    return {"fr": fr, "ar": ar}


def _lire_csv(chemin: Path) -> list[dict]:
    return lire(chemin) if chemin.exists() else []


# --- 1. détection de langue -------------------------------------------------------

def detecter_langue(question: str) -> str:
    if re.search(r"[؀-ۿ]", question):
        mots = {normaliser_ar(m) for m in re.findall(r"[^\W\d_]+", question)}
        return "tunisien" if mots & MARQUEURS_TUN_AR else "ar"
    mots = {m.lower() for m in re.findall(r"\w+", question)}
    if est_arabizi(question) or mots & MARQUEURS_ARABIZI:
        return "arabizi"
    return "fr"


# --- 2. translittération arabizi -> arabe ------------------------------------------

def translitterer_mot(mot: str) -> str:
    m, sortie, i = mot.lower(), [], 0
    while i < len(m):
        if m[i:i + 2] in DIGRAMMES:
            sortie.append(DIGRAMMES[m[i:i + 2]])
            i += 2
            continue
        c = m[i]
        if c == "a" and i == len(m) - 1 and i > 0:
            sortie.append("ة")            # « 5edma » -> خدمة : a final = tâ marbûta
        else:
            sortie.append(LETTRES.get(c, c))
        i += 1
    return "".join(sortie)


def translitterer_arabizi(question: str, est_francais) -> str:
    """Translittère les mots arabizi ; garde les mots français connus (« congé »)."""
    def mot(x: re.Match) -> str:
        w = x.group(0)
        if w.isdigit():
            return w                      # « 5 ayem » : 5 est un nombre, pas la lettre خ
        if w.lower() in MARQUEURS_ARABIZI or any(c.isdigit() for c in w):
            return translitterer_mot(w)
        return w if est_francais(w) else translitterer_mot(w)
    return re.sub(r"[^\W_]+", mot, question)


# --- 3 à 6 : découpage, mots vides, normalisation, lexiques, racinisation -----------

def decouper(texte: str) -> list[str]:
    """Jetons = suites de lettres ou de chiffres (« l'article » -> « l », « article »)."""
    return re.findall(r"[^\W_]+", texte)


def noms_propres(question: str) -> set[str]:
    """Mots en majuscule hors début de phrase (Sousse, SONEDE), sous forme normalisée."""
    sortie = set()
    for m in re.finditer(r"[^\W\d_]+", question):
        if m.group(0)[:1].isupper() and question[:m.start()].strip():
            sortie.add(normaliser_fr(m.group(0)))
    return sortie


def script_de(jeton: str) -> str:
    return "ar" if re.search(r"[؀-ۿ]", jeton) else "fr"


def retirer_mots_vides(jetons: list[str], mots_vides: dict[str, set[str]]) -> list[str]:
    garde = []
    for j in jetons:
        cle = _sans_diacritiques(j) if script_de(j) == "ar" else j.lower()
        if cle not in mots_vides[script_de(j)]:
            garde.append(j)
    return garde


def normaliser_jeton(jeton: str) -> str:
    return normaliser_ar(jeton) if script_de(jeton) == "ar" else normaliser_fr(jeton)


def normaliser(jetons: list[str]) -> list[str]:
    return [normaliser_jeton(j) for j in jetons]


def raciniser_ar(jetons: list[str]) -> list[str]:
    return [reduire_ar(j)[1] if script_de(j) == "ar" else j for j in jetons]


@dataclass
class Config:
    """Étapes actives (pour l'ablation). Par défaut : pipeline complet."""
    mots_vides: bool = True
    normalisation: bool = True
    symspell: bool = True
    synonymes: bool = True
    complet: bool = True      # langue 4 voies + translittération + lexiques/sigles + racinisation
    nom: str = "pipeline complet"
    arabizi: bool = True      # False : l'arabizi est traité comme du français (diagnostic)


@dataclass
class Pipeline:
    config: Config = field(default_factory=Config)

    def __post_init__(self):
        self.mots_vides = charger_mots_vides() if self.config.mots_vides else {"fr": set(), "ar": set()}
        self.correcteur = Correcteur(mots_vides=charger_mots_vides())
        self.lexique_tun = {}
        for r in _lire_csv(LEXIQUE_TUNISIEN):
            self.lexique_tun[normaliser_ar(r["tunisien"].strip())] = normaliser_ar(r["standard"].strip())
        self.synonymes: dict[str, set[str]] = {}
        for r in _lire_csv(SYNONYMES):
            a, b = (self._forme_index(r["terme"]), self._forme_index(r["synonyme"]))
            self.synonymes.setdefault(a, set()).add(b)
            self.synonymes.setdefault(b, set()).add(a)
        self.index = {"fr": self._indexer(FR, intitule_fr, "texte_fr"),
                      "ar": self._indexer(AR, intitule_ar, "texte_ar")}

    # Traitement commun question / corpus (étapes 3, 4, 6).
    def _forme_index(self, mot: str) -> str:
        j = normaliser_jeton(mot) if self.config.normalisation else mot
        return reduire_ar(j)[1] if (self.config.complet and script_de(j) == "ar") else j

    def jetons_document(self, texte: str) -> list[str]:
        j = decouper(texte)
        j = retirer_mots_vides(j, self.mots_vides)
        if self.config.normalisation:
            j = normaliser(j)
        if self.config.complet:
            j = raciniser_ar(j)
        return j

    def _indexer(self, chemin, intitule, colonne):
        articles, docs = [], []
        for r in lire(chemin):
            texte = r[colonne].strip()
            lab = intitule(texte)
            if lab:
                articles.append({"article": lab, "texte": texte, "page": r["page"]})
                docs.append((lab, self.jetons_document(texte)))
        return {"articles": articles, "bm": Bm25(docs)}

    # --- étapes propres à la question ---------------------------------------------

    def appliquer_lexiques(self, jetons: list[str]) -> list[str]:
        """Tunisien -> standard, puis sigles (sans répéter le mot qui précède : « contrat CDI »)."""
        sortie = []
        for j in jetons:
            j = self.lexique_tun.get(j, j)
            sigle = j.upper()
            if sigle in SIGLES:
                developpe = self.jetons_document(SIGLES[sigle])
                precedent = sortie[-1] if sortie else ""
                corrige = self.correcteur.corriger_mot(precedent, "fr") if precedent else None
                if developpe and precedent and normaliser_fr(corrige or precedent) == developpe[0]:
                    developpe = developpe[1:]
                sortie.extend(developpe)
            else:
                sortie.append(j)
        return sortie

    def corriger_jetons(self, jetons: list[str], intacts: set[str] = frozenset()) -> tuple[list[str], list[dict]]:
        """`intacts` : jetons à ne pas corriger (noms propres repérés sur la question d'origine)."""
        sortie, corrections = [], []
        for j in jetons:
            if j in intacts:
                sortie.append(j)
                continue
            propose = self.correcteur.corriger_jeton(j, script_de(j), deja_reduit=self.config.complet)
            if propose and propose != j:
                corrections.append({"type": "orthographe", "avant": j, "apres": propose})
                sortie.append(self._forme_index(propose))
            else:
                sortie.append(j)
        return sortie, corrections

    def ajouter_synonymes(self, jetons: list[str]) -> list[str]:
        ajouts = [s for j in jetons for s in sorted(self.synonymes.get(j, ())) if s not in jetons]
        return jetons + list(dict.fromkeys(ajouts))

    # --- chaîne complète ----------------------------------------------------------

    def traiter(self, question: str) -> dict:
        etapes = []
        langue = detecter_langue(question) if self.config.complet else (
            "ar" if re.search(r"[؀-ۿ]", question) else "fr")
        if langue == "arabizi" and not self.config.arabizi:
            langue = "fr"
        etapes.append({"etape": "1. langue", "sortie": langue})

        texte = question
        if self.config.complet and langue == "arabizi":
            texte = translitterer_arabizi(question, self.correcteur.est_mot_francais)
        etapes.append({"etape": "2. translittération arabizi", "sortie": texte})

        jetons = retirer_mots_vides(decouper(texte), self.mots_vides)
        etapes.append({"etape": "3. mots vides", "sortie": " ".join(jetons)})

        if self.config.normalisation:
            jetons = normaliser(jetons)
        etapes.append({"etape": "4. normalisation", "sortie": " ".join(jetons)})

        if self.config.complet:
            jetons = self.appliquer_lexiques(jetons)
        etapes.append({"etape": "5. lexique tunisien et sigles", "sortie": " ".join(jetons)})

        if self.config.complet:
            jetons = raciniser_ar(jetons)
        etapes.append({"etape": "6. racinisation arabe", "sortie": " ".join(jetons)})

        corrections = []
        if self.config.symspell:
            jetons, corrections = self.corriger_jetons(jetons, noms_propres(question))
        etapes.append({"etape": "7. correction SymSpell", "sortie": " ".join(jetons)})

        if self.config.synonymes:
            jetons = self.ajouter_synonymes(jetons)
        etapes.append({"etape": "8. synonymes", "sortie": " ".join(jetons)})
        return {"langue_detectee": langue, "jetons": jetons, "etapes": etapes, "corrections": corrections}

    def _scores(self, corpus: str, jetons: list[str]) -> list[float]:
        bm = self.index[corpus]["bm"]
        scores = [0.0] * bm.n
        for terme in set(jetons):
            if terme not in bm.df:
                continue
            idf = math.log(1 + (bm.n - bm.df[terme] + 0.5) / (bm.df[terme] + 0.5))
            for i, c in enumerate(bm.tf):
                f = c.get(terme, 0)
                if f:
                    scores[i] += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * bm.dl[i] / bm.avgdl))
        return scores

    def classer(self, jetons: list[str], langue: str) -> list[tuple[dict, float]]:
        """Articles triés par score (un par intitulé).

        Arabizi : les jetons arabes interrogent le corpus AR, les mots français gardés le
        corpus FR ; les scores sont additionnés par numéro d'article (corpus alignés).
        """
        if langue == "arabizi":
            groupes = {"ar": [j for j in jetons if script_de(j) == "ar"],
                       "fr": [j for j in jetons if script_de(j) == "fr"]}
        else:
            groupes = {("fr" if langue == "fr" else "ar"): jetons}
        total: dict[str, float] = {}
        texte: dict[str, dict] = {}
        for corpus in ("ar", "fr"):
            js = groupes.get(corpus)
            if not js:
                continue
            # Un article découpé en plusieurs lignes garde sa meilleure ligne (comme la démo).
            meilleur: dict[str, tuple[dict, float]] = {}
            for art, s in zip(self.index[corpus]["articles"], self._scores(corpus, js)):
                if s > 0 and s > meilleur.get(art["article"], (None, 0.0))[1]:
                    meilleur[art["article"]] = (art, s)
            for lab, (art, s) in meilleur.items():
                total[lab] = total.get(lab, 0.0) + s
                texte[lab] = art          # le texte FR est affiché s'il existe (traité en dernier)
        return sorted(((texte[l], s) for l, s in total.items()), key=lambda x: -x[1])

    def repondre(self, question: str, k: int = 3) -> dict:
        """Sortie : question_originale, question_corrigee (lisible, pour « Vouliez-vous dire »),
        corrections, langue (corpus interrogé), langue_detectee, etapes (mode debug),
        abstention et candidats."""
        traitement = self.traiter(question)
        langue = traitement["langue_detectee"]
        classes = self.classer(traitement["jetons"], langue)
        corpus = "fr" if langue == "fr" else "ar"
        abstention = not classes or classes[0][1] < SEUIL_SCORE_MIN
        candidats = [] if abstention else [{**a, "score": round(s, 2)} for a, s in classes[:k]]
        # Version lisible de la correction (mêmes dictionnaires et règles que l'étape 7).
        if self.config.symspell and langue != "arabizi":
            lisible = self.correcteur.corriger(question, corpus)
        else:
            lisible = {"question_originale": question, "question_corrigee": question, "corrections": []}
        return {**lisible, "langue": corpus, "langue_detectee": langue,
                "etapes": traitement["etapes"], "abstention": abstention, "candidats": candidats}


_PIPELINE: Pipeline | None = None


def pipeline() -> Pipeline:
    """Instance partagée du pipeline complet (index construits une seule fois)."""
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = Pipeline()
    return _PIPELINE
