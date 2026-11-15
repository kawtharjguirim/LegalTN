"""Pré-annotation NER par règles (gazetteers + expressions régulières), FR et AR.

Schéma : ``data/dev/ner_guide_annotation_v1.md`` (ROLE, INSTITUTION, DELAI, MONTANT).
Ces annotations sont *automatiques* : elles servent de corpus d'entraînement
« silver » et de pré-remplissage à corriger. Elles ne sont jamais un gold.

Une entité est un triplet ``(debut, fin, type)`` en positions de caractères
(base 0, fin exclue), sans chevauchement.
"""

from __future__ import annotations

import re

TYPES = ("ROLE", "INSTITUTION", "DELAI", "MONTANT")

# ---------------------------------------------------------------- français
_NOMBRE_FR = (
    r"(?:\d+(?:[.,]\d+)?|"
    r"(?:(?:un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|treize|quatorze|"
    r"quinze|seize|vingt|trente|quarante|cinquante|soixante|cent|cents|mille)"
    r"(?:[\s-]+(?:et[\s-]+)?(?:un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|"
    r"treize|quatorze|quinze|seize|vingt|vingts|trente|quarante|cinquante|soixante|cent|cents|"
    r"mille))*))"
)
_DET_FR = r"(?:le|la|les|l['’]|tout|toute|tous|toutes|chaque|aucun|aucune|un|une|son|sa|ses|leur|leurs|du|des|au|aux)"

_ROLES_FR = [
    r"chefs? d['’](?:entreprise|établissement)s?", r"ma[iî]tres? d['’]apprentissage",
    r"conseillers? prud['’]hom(?:me|aux|mes)", r"inspecteurs? (?:général |régional )?du travail",
    r"contr[oô]leurs? du travail", r"médecins? du travail", r"délégués? du personnel",
    r"représentants? (?:du personnel|des travailleurs|des employeurs)",
    r"employeurs?", r"travailleu(?:r|rs|se|ses)", r"salarié(?:e|s|es)?", r"apprenti(?:e|s|es)?",
    r"ouvri(?:er|ers|ère|ères)", r"employé(?:e|s|es)?", r"entrepreneurs?",
    r"sous-entrepreneurs?", r"tâcherons?", r"adjudicataires?", r"enfants?", r"femmes?",
    r"jeunes travailleurs", r"parties", r"intéressé(?:e|s|es)?", r"agents?", r"juges?",
    r"gouverneurs?", r"arbitres?", r"délégués?",
]
_INSTITUTIONS_FR = [
    r"caisse nationale (?:de (?:la )?sécurité sociale|de retraite et de prévoyance sociale)",
    r"inspection (?:générale |médicale )?du travail", r"conseils? de prud['’]hommes?",
    r"tribunal(?: de première instance| cantonal| administratif)?", r"cour de cassation",
    r"secrétaire d['’]etat(?: (?:à|aux?) [\w ’'-]{3,60}?)?(?=[,.;:]| et | ou | qui | pris| après| sur)",
    r"secrétariat d['’]etat(?: (?:à|aux?) [\w ’'-]{3,60}?)?(?=[,.;:]| et | ou | qui | pris| après| sur)",
    r"ministre (?:chargé|des|de la|de l['’])[\w ’'-]{3,60}?(?=[,.;:]| et | ou | qui | pris| après| sur)",
    r"ministère (?:chargé|des|de la|de l['’])[\w ’'-]{3,60}?(?=[,.;:]| et | ou | qui | pris| après| sur)",
    r"office (?:de la formation professionnelle et de l['’]emploi|national [\w ’'-]{3,40}?)(?=[,.;:]| et | ou | qui )",
    r"commission (?:consultative|nationale|régionale|paritaire|de contrôle)[\w ’'-]{0,60}?(?=[,.;:]| et | ou | qui | est | sont )",
    r"conseil (?:national|supérieur|de la formation)[\w ’'-]{0,60}?(?=[,.;:]| et | ou | qui | est | sont )",
    r"organisations? (?:professionnelles?|syndicales?) (?:d['’]employeurs|de travailleurs|les plus représentatives)(?: et de travailleurs)?",
    r"syndicats? professionnels?", r"comités? consultatifs? d['’]entreprise",
]
_UNITES_DELAI_FR = r"(?:jours?|journées?|semaines?|mois|ans?|années?|trimestres?)"
_UNITES_MONTANT_FR = r"(?:dinars?|millimes?|D\b|heures?|pour\s?cent|%|enfants|travailleurs|salariés)"


def _compiler_fr():
    roles = "|".join(_ROLES_FR)
    inst = "|".join(_INSTITUTIONS_FR)
    return [
        ("INSTITUTION", re.compile(rf"\b(?:(?:la|le|les|l['’]|du|des|au|aux)\s?)?(?:{inst})", re.I)),
        ("ROLE", re.compile(rf"\b(?:{_DET_FR}\s?)(?:{roles})\b", re.I)),
        ("MONTANT", re.compile(
            rf"\b(?:âgée?s? de (?:moins de |plus de )?)?{_NOMBRE_FR}\s*{_UNITES_MONTANT_FR}"
            r"(?:\s+(?:par|au)\s+(?:jour|semaine|mois|an))?", re.I)),
        ("DELAI", re.compile(
            rf"\b(?:(?:dans (?:un délai (?:de|d['’]|maximum de|minimum de)|les|le délai de)|"
            rf"au (?:moins|plus tard|plus|minimum|maximum)|pendant|durant|avant|après|"
            rf"à l['’]expiration d['’]un délai de|d['’]une durée (?:de|maximum de)|de)\s+)?"
            rf"{_NOMBRE_FR}\s+{_UNITES_DELAI_FR}(?:\s+(?:avant|après|au moins|au plus|à compter))?",
            re.I)),
    ]


# ---------------------------------------------------------------- arabe
# Proclitiques détachés de l'entité : و ف ب ل ك (et leurs combinaisons).
_PROCLITIQUE = r"(?:(?<=\s)|(?<=^)|(?<=[(«\"]))(?:[وف]?[بلك]?)"
_NOMBRE_AR = (
    r"(?:\d+|(?:واحد|واحدة|اثنين|اثنان|ثلاثة|ثلاث|أربعة|أربع|خمسة|خمس|ستة|ست|سبعة|سبع|ثمانية|"
    r"ثماني|ثمان|تسعة|تسع|عشرة|عشر|أحد عشر|اثني عشر|خمسة عشر|ثمانية عشر|عشرين|عشرون|ثلاثين|"
    r"أربعين|خمسين|ستين|مائة|مائتي|ألف|نصف|ربع)(?:\s+(?:و|عشر|عشرة)\s*\S+)?)"
)
_ROLES_AR = [
    r"(?:ال)?مؤجر(?:ين|ون)?", r"(?:ال)?عامل(?:ة|ين|ون)?", r"(?:ال)?عمال", r"(?:ال)?عملة",
    r"(?:ال)?أجير|(?:ال)?أجراء", r"(?:ال)?متعلم(?:ين|ون)?", r"(?:ال)?مشغل(?:ين)?",
    r"رؤساء المؤسسات", r"رئيس المؤسسة", r"صاحب (?:ال)?مؤسسة", r"صاحب العمل",
    r"متفقد(?:ي)? الشغل", r"مراقب(?:ي)? الشغل", r"طبيب الشغل",
    r"(?:ال)?أطفال", r"(?:ال)?طفل", r"(?:ال)?نساء", r"(?:ال)?مرأة", r"(?:ال)?أحداث",
    r"مندوب(?:ي)? العملة", r"نواب العملة", r"(?:ال)?مقاول(?:ين)?(?: الفرعي)?", r"(?:ال)?طرفين|(?:ال)?طرفان",
    r"(?:ال)?أطراف", r"المدعى عليه", r"(?:ال)?مدعي", r"(?:ال)?قاضي", r"الحكام", r"الولاة", r"الوالي",
]
_INSTITUTIONS_AR = [
    r"الصندوق الوطني للضمان الاجتماعي", r"الصندوق الوطني للتقاعد والحيطة الاجتماعية",
    r"تفقدية الشغل", r"التفقدية العامة للشغل", r"(?:ال)?محكمة(?: الابتدائية| الناحية| التعقيب)?",
    r"مجلس (?:ال)?(?:أحبار|عرف)(?:ين)?(?: الشغل)?", r"دائرة الشغل",
    r"كاتب الدولة(?: [^\s،.؛]+){0,4}?(?=[،.؛]| و| بعد| أو)", r"(?:ال)?وزير المكلف ب[^\s،.؛]+(?: [^\s،.؛]+){0,2}",
    r"(?:ال)?لجنة (?:ال)?(?:استشارية|وطنية|جهوية|متناصفة)(?: [^\s،.؛]+){0,3}?(?=[،.؛]| و| أو| التي)",
    r"(?:ال)?منظمات (?:ال)?(?:مهنية|نقابية)(?: (?:ل|لل)(?:أعراف|مؤجرين|عملة|عمال))?",
    r"ديوان التكوين المهني والتشغيل", r"(?:ال)?نقابات? (?:ال)?مهنية",
]
_UNITES_DELAI_AR = r"(?:يوما|يوم|أيام|أسبوعا|أسبوع|أسابيع|شهرا|شهر|أشهر|شهور|سنة|سنوات|أعوام|عاما)"
_UNITES_MONTANT_AR = r"(?:دينارا|دينار|دنانير|مليما|مليم|ساعة|ساعات|بالمائة|في المائة|%)"


def _compiler_ar():
    # « للمؤجر » = ل + (ا)لمؤجر : l'article assimilé devient « ل » après la préposition.
    roles = "|".join(_ROLES_AR).replace("(?:ال)?", "(?:ال|ل)?")
    inst = "|".join(_INSTITUTIONS_AR).replace("(?:ال)?", "(?:ال|ل)?")
    fin = r"(?![\w])"
    return [
        ("INSTITUTION", re.compile(rf"{_PROCLITIQUE}((?:{inst})){fin}")),
        ("ROLE", re.compile(rf"{_PROCLITIQUE}((?:كل |أي )?(?:{roles})){fin}")),
        ("MONTANT", re.compile(rf"{_PROCLITIQUE}((?:{_NOMBRE_AR})\s+{_UNITES_MONTANT_AR}){fin}")),
        ("DELAI", re.compile(
            rf"{_PROCLITIQUE}((?:(?:في )?(?:أجل|ظرف|خلال|مدة|أقصاه|أدناه|على الأقل)\s+(?:أقصاه\s+|لا يتجاوز\s+)?)?"
            rf"(?:{_NOMBRE_AR})\s+{_UNITES_DELAI_AR}(?:\s+على الأقل)?){fin}")),
        # Duel : « الشهرين », « يومين », « سنتين ».
        ("DELAI", re.compile(
            rf"{_PROCLITIQUE}((?:(?:في |خلال |أجل )?(?:ال)?(?:يومين|أسبوعين|شهرين|سنتين|عامين))"
            rf"(?:\s+(?:المواليين|المواليين|التاليين))?){fin}")),
    ]


_REGLES = {"fr": _compiler_fr(), "ar": _compiler_ar()}


def annoter(phrase: str, langue: str) -> list[tuple[int, int, str]]:
    """Entités trouvées par les règles, la plus longue gagnant en cas de chevauchement."""
    candidats = []
    for type_, rx in _REGLES[langue]:
        for m in rx.finditer(phrase):
            g = 1 if langue == "ar" else 0
            debut, fin = m.span(g)
            # Bornes propres : pas d'espace ni de ponctuation en bord d'entité.
            while debut < fin and phrase[debut] in " ،,.;:":
                debut += 1
            while fin > debut and phrase[fin - 1] in " ،,.;:":
                fin -= 1
            if fin - debut >= 2:
                candidats.append((debut, fin, type_))
    candidats.sort(key=lambda e: (-(e[1] - e[0]), e[0]))
    retenus: list[tuple[int, int, str]] = []
    for e in candidats:
        if all(e[1] <= r[0] or e[0] >= r[1] for r in retenus):
            retenus.append(e)
    return sorted(retenus)


def vers_texte(entites: list[tuple[int, int, str]]) -> str:
    """Format du guide : ``debut|fin|TYPE;debut|fin|TYPE``."""
    return ";".join(f"{d}|{f}|{t}" for d, f, t in entites)


def depuis_texte(champ: str) -> list[tuple[int, int, str]]:
    if not isinstance(champ, str) or not champ.strip():
        return []
    sortie = []
    for bloc in champ.split(";"):
        d, f, t = bloc.strip().split("|")
        if t not in TYPES:
            raise ValueError(f"type inconnu : {t}")
        sortie.append((int(d), int(f), t))
    return sorted(sortie)


def lisible(phrase: str, entites: list[tuple[int, int, str]]) -> str:
    """« [l'employeur]ROLE doit ... » pour faciliter la relecture."""
    morceaux, pos = [], 0
    for d, f, t in sorted(entites):
        morceaux += [phrase[pos:d], f"[{phrase[d:f]}]{t}"]
        pos = f
    morceaux.append(phrase[pos:])
    return "".join(morceaux)
