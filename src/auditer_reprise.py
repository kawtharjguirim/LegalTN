"""Contrôles en lecture seule des fichiers récupérés ; aucune mesure de modèle.

Depuis la racine : python src/auditer_reprise.py
Le rapport JSON est écrit sur stdout. Seules les définitions de normalisation
auditées du notebook v5 sont exécutées, sans chargement ni export du notebook.
"""

import ast
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
EMPREINTES_RECUPEREES = {
    "data/processed/texte_travail.json": "e17a630477073bda2e5e4970b5637a78de8f839c67cf2a27b70842bfb1e441f1",
    "data/processed/articles_fr.csv": "a75e4c21c679796a1e9ff04dc071fdc08c698004ddc3cd198d8c54fb0dca122b",
    "data/processed/articles_fr_corrige.csv": "ac627cfc3806ec10a8061bdd5df2bc5f17527195112dc51449d8a463e8d8e071",
    "data/dev/questions_dev_v2.csv": "9c616a6c73e36b5cfe8c36429f9568bbfa194f8e5f4fa5c84f7994273d59deb8",
    "notebooks/01_data_exploration.ipynb": "58157d3a196a6c67fd82df7ab44cb2b43f8c04ef2c0728cbc168ddb6cd8e6e89",
    "docs/Guide_Revue_Bronze.pdf": "a67a547bbd80cdd57aa24db4984a44112fcc7e9594d4f294c00ff5846c479540",
    "notebooks/03_alignement_fr_ar.ipynb": "9e3e25e9392d64db2fefd5093542f6923606b6677465b5ec048efe7504f14bde",
    "notebooks/03_alignement_fr_ar_v4.ipynb": "f81b76b791b31bd2838fd2ac696389bc2809b8cac7468a26e8ba14895df89aa9",
    "notebooks/03_alignement_fr_ar_v5.ipynb": "7214f6a6702145513cae58060922a81705e66351f4c2afcef4b2fa206f1ce0df",
    "data/processed/articles_ar.csv": "77fe24b3d3ffc5923fd42fe4298521ebdbcec5f7af001ccd576a90fa69846022",
    "data/raw/arabic/majallat_al_shughl_2019.pdf": "de17529ea734212b6efcec0d796762f39fefbf97455a573ca402bf83c74bc467",
}


def sha256(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def lire_csv(chemin):
    with chemin.open(encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier)
        if not lecteur.fieldnames or len(set(lecteur.fieldnames)) != len(lecteur.fieldnames):
            raise ValueError(f"En-tête absent ou colonnes dupliquées : {chemin}")
        lignes = list(lecteur)
    for numero, ligne in enumerate(lignes, 2):
        if None in ligne or any(valeur is None for valeur in ligne.values()):
            raise ValueError(f"Ligne CSV mal formée : {chemin}:{numero}")
    return lignes


def doublons(lignes, champ):
    return {cle: n for cle, n in Counter(l[champ] for l in lignes).items() if n > 1}


def charger_cles_alignement():
    """Charge uniquement les définitions auditées de la cellule 2 du notebook v5.

    Ne lance ni les entrées/sorties ni le reste du notebook. Ce chargeur est
    réservé à cette source locale inspectée, pas à des notebooks arbitraires.
    """
    chemin = RACINE / "notebooks/03_alignement_fr_ar_v5.ipynb"
    notebook = json.loads(chemin.read_bytes())
    arbre = ast.parse("".join(notebook["cells"][2]["source"]))
    constantes = {"SUFFIXES_AR", "SUFFIXES_FR", "RE_TETE_FR"}
    fonctions = {"cle_ar", "cle_fr"}
    selection = []
    trouves = set()
    for noeud in arbre.body:
        if isinstance(noeud, ast.FunctionDef) and noeud.name in fonctions:
            selection.append(noeud)
            trouves.add(noeud.name)
        elif isinstance(noeud, ast.Assign) and len(noeud.targets) == 1:
            cible = noeud.targets[0]
            if isinstance(cible, ast.Name) and cible.id in constantes:
                selection.append(noeud)
                trouves.add(cible.id)
    if trouves != constantes | fonctions:
        raise ValueError("Structure des règles v5 modifiée : nouvelle inspection nécessaire.")
    espace = {"re": re}
    exec(compile(ast.Module(body=selection, type_ignores=[]), str(chemin), "exec"), espace)
    return espace["cle_ar"], espace["cle_fr"]


def bilan_fr(lignes):
    return {
        "entrees": len(lignes),
        "identifiants_distincts": len({l["article_id"] for l in lignes}),
        "identifiants_repetes": doublons(lignes, "article_id"),
        "textes_vides_indices": [i for i, l in enumerate(lignes) if not l["texte_fr"].strip()],
        "textes_identiques_en_exces": len(lignes) - len({l["texte_fr"] for l in lignes}),
        "longueurs_incoherentes_indices": [
            i for i, l in enumerate(lignes) if int(l["longueur"]) != len(l["texte_fr"])
        ],
        "numeros_sans_ligne_individuelle_1_446": sorted(
            set(range(1, 447)) - {int(l["numero"]) for l in lignes}
        ),
        "limite": "Les numéros répétés peuvent désigner des suffixes ou des textes distincts. "
                  "Les absences peuvent relever de plages abrogées ; aucune correction automatique.",
    }


def auditer_alignement_complet():
    """Décrit le corpus récupéré et un export réel, sans supposer de gold indépendant."""
    dossier = RACINE / "data/processed"
    arabes = lire_csv(dossier / "articles_ar.csv")
    bilan = {
        "articles_ar": len(arabes),
        "identifiants_dupliques": doublons(arabes, "article_id"),
        "numeros_absents_1_446": sorted(set(range(1, 447)) - {int(a["numero"]) for a in arabes}),
        "articles_sans_chapitre": [a["article_id"] for a in arabes if not a["chapitre"]],
        "articles_abroges": sum(a["abroge"] == "True" for a in arabes),
        "articles_marques_plage": sum(a["plage"] == "True" for a in arabes),
        "longueurs_incoherentes": [
            {"article_ar": a["article_id"], "longueur_stockee": int(a["longueur"]),
             "longueur_texte": len(a["texte_ar"])}
            for a in arabes if int(a["longueur"]) != len(a["texte_ar"])
        ],
        "metriques_test_independant": {
            "precision": None, "rappel": None, "f1": None,
            "raison": "Référence indépendante absente ; contrôles de développement seulement.",
        },
    }
    chemin = dossier / "alignement_fr_ar_v6.csv"
    if not chemin.exists():
        bilan["export_v6_present"] = False
        return bilan
    nouveau = lire_csv(chemin)
    ancien = lire_csv(dossier / "alignement_fr_ar.csv")
    bilan["export_v6_present"] = True
    bilan["statuts_v6"] = dict(Counter(r["statut"] for r in nouveau))
    bilan["lignes_v6"] = len(nouveau)
    bilan["controles_annees"] = [
        {"article_ar": r["article_ar"], "controle": r["controle"]}
        for r in nouveau if r["controle"]
    ]
    bilan["apparies_avec_drapeau_abroge"] = [
        r["article_ar"] for r in nouveau if r["statut"] == "apparié" and r["abroge"] == "True"
    ]
    bilan["etiquettes_fr_sans_suffixe"] = [
        {"article_ar": r["article_ar"], "article_fr": r["article_fr"], "cle": r["cle"]}
        for r in nouveau
        if r["statut"] == "apparié" and (" " in r["cle"] or "-" in r["cle"])
        and r["article_fr"] == "FR-" + r["cle"].split()[0].split("-")[0]
    ]
    memes_positions = len(ancien) == len(nouveau) and all(
        all(a[k] == b[k] for k in ("article_ar", "article_fr", "page_ar", "page_fr", "fr_ligne", "cle", "statut"))
        for a, b in zip(ancien, nouveau)
    )
    bilan["appariements_et_statuts_identiques_export_heritage"] = memes_positions
    bilan["differences_export_heritage"] = [
        {"ligne": i, "article_ar": b["article_ar"],
         "champs": {k: {"avant": a[k], "apres": b.get(k)} for k in a if a[k] != b.get(k)}}
        for i, (a, b) in enumerate(zip(ancien, nouveau)) if a != b
    ] if memes_positions else None
    index_ar = {a["article_id"]: a for a in arabes}
    index_export = {}
    for ligne in nouveau:
        if ligne["article_ar"]:
            index_export.setdefault(ligne["article_ar"], []).append(ligne)
    bilan["controle_dev_export_reel"] = {}
    for nom in ("alignement_dev_v1.csv", "alignement_dev_v2_a_annoter.csv"):
        refs = lire_csv(RACINE / "data/dev" / nom)
        ecarts = []
        for r in refs:
            candidats = index_export.get(r["article_ar"], [])
            if (
                r["article_ar"] not in index_ar
                or index_ar[r["article_ar"]]["page"] != r["page_ar"]
                or len(candidats) != 1
                or candidats[0]["statut"] != "apparié"
                or any(candidats[0][k] != r[k] for k in ("article_fr", "page_fr", "fr_ligne"))
            ):
                ecarts.append(r["dev_id"])
        bilan["controle_dev_export_reel"][nom] = {
            "references": len(refs), "concordantes": len(refs) - len(ecarts), "ecarts": ecarts,
        }
    artefacts = (
        "notebooks/03_alignement_fr_ar_v6.ipynb", "src/executer_alignement.py",
        "data/processed/articles_ar.csv", "data/processed/articles_fr_corrige.csv",
        "data/processed/alignement_fr_ar.csv", "data/processed/alignement_fr_ar_v6.csv",
        "data/processed/alignement_resume_v6.json",
        "data/processed/alignement_echantillon_image_v6.csv",
    )
    bilan["empreintes_execution"] = {nom: sha256(RACINE / nom) for nom in artefacts}
    return bilan


def auditer():
    rapport = {
        "nature": "Contrôles de fichiers ; ni évaluation de modèle ni validation humaine.",
        "indices": "fr_ligne et indices de corpus commencent à zéro, hors en-tête CSV.",
        "integrite_recuperation": {
            nom: {
                "sha256_actuel": sha256(RACINE / nom),
                "sha256_recu": attendu,
                "identique": sha256(RACINE / nom) == attendu,
            }
            for nom, attendu in EMPREINTES_RECUPEREES.items()
        },
    }
    pages = json.loads((RACINE / "data/processed/texte_travail.json").read_bytes())
    if not isinstance(pages, dict) or any(not isinstance(v, str) for v in pages.values()):
        raise ValueError("Le texte de travail doit associer des clés de page à des chaînes.")
    rapport["texte_travail"] = {
        "pages": len(pages),
        "cles_exactement_1_291": set(pages) == {str(i) for i in range(1, 292)},
        "pages_vides": [k for k, v in pages.items() if not v.strip()],
    }
    original = lire_csv(RACINE / "data/processed/articles_fr.csv")
    corrige = lire_csv(RACINE / "data/processed/articles_fr_corrige.csv")
    rapport["corpus_fr"] = {"original": bilan_fr(original), "corrige": bilan_fr(corrige)}
    memes_positions = len(original) == len(corrige) and all(
        all(a[k] == b[k] for k in ("article_id", "numero", "page"))
        for a, b in zip(original, corrige)
    )
    rapport["comparaison_fr"] = {
        "ordre_identifiants_numeros_pages_identiques": memes_positions,
        "indices_texte_modifie": [
            i for i, (a, b) in enumerate(zip(original, corrige)) if a["texte_fr"] != b["texte_fr"]
        ] if memes_positions else None,
        "limite": "Comparaison de versions, pas validation des corrections sur les images.",
    }
    rapport["references_alignement_dev"] = {}
    for nom in ("alignement_dev_v1.csv", "alignement_dev_v2_a_annoter.csv"):
        references = lire_csv(RACINE / "data/dev" / nom)
        non_resolues = []
        for r in references:
            i = int(r["fr_ligne"])
            if not 0 <= i < len(corrige) or (
                corrige[i]["article_id"], corrige[i]["page"]
            ) != (r["article_fr"], r["page_fr"]):
                non_resolues.append(r["dev_id"])
        rapport["references_alignement_dev"][nom] = {
            "references": len(references),
            "identifiant_et_page_concordants": len(references) - len(non_resolues),
            "non_resolues": non_resolues,
            "limite": "Ne vérifie ni le suffixe dans le texte ni l'équivalence AR/FR.",
        }
    cle_ar, cle_fr = charger_cles_alignement()
    index_fr = {}
    hors_code = []
    non_reconnus = []
    for i, ligne in enumerate(corrige):
        if int(ligne["page"]) in {288, 289}:
            hors_code.append(i)
            continue
        cle = cle_fr(ligne["texte_fr"])
        if cle is None:
            non_reconnus.append(i)
        else:
            index_fr.setdefault(cle, []).append(i)
    controles_dev = {}
    for nom in ("alignement_dev_v1.csv", "alignement_dev_v2_a_annoter.csv"):
        references = lire_csv(RACINE / "data/dev" / nom)
        ecarts = []
        for r in references:
            cle = cle_ar(r["article_ar"])
            obtenues = index_fr.get(cle, [])
            if obtenues != [int(r["fr_ligne"])]:
                ecarts.append({
                    "dev_id": r["dev_id"], "cle_calculee": cle,
                    "lignes_obtenues": obtenues, "ligne_attendue": int(r["fr_ligne"]),
                })
        controles_dev[nom] = {
            "references": len(references), "lignes_retrouvees": len(references) - len(ecarts),
            "ecarts": ecarts,
        }
    rapport["regles_alignement_v5"] = {
        "indices_hors_code": hors_code,
        "cles_fr_distinctes_dans_code": len(index_fr),
        "indices_sans_cle": non_reconnus,
        "cles_ambigues": {k: v for k, v in index_fr.items() if len(v) > 1},
        "controle_dev": controles_dev,
        "limite": "Règles originales exécutées sur les identifiants des références de développement "
                  "héritées ; ce contrôle seul ne mesure ni rappel global ni résultat de test indépendant.",
    }
    candidats = lire_csv(RACINE / "data/dev/obligations_candidats_dev_v1.csv")
    citations = []
    for c in candidats:
        if not c["phrase"].strip():
            citations.append({"id": c["obligation_id"], "raison": "phrase vide"})
            continue
        correspondances = [
            i for i, l in enumerate(corrige)
            if l["article_id"] == c["article_fr"] and l["page"] == c["page_fr"]
            and c["phrase"] in l["texte_fr"]
        ]
        if len(correspondances) != 1:
            citations.append({"id": c["obligation_id"], "indices_correspondants": correspondances})
    rapport["obligations_dev"] = {
        "candidats": len(candidats),
        "citations_non_uniques_ou_absentes": citations,
        "champs_annotation_remplis": {
            k: sum(bool(l[k].strip()) for l in candidats)
            for k in ("qui", "modal", "quoi", "quand", "commentaire")
        },
        "limite": "La présence d'un extrait ne prouve pas qu'il exprime une obligation.",
    }
    questions = lire_csv(RACINE / "data/dev/questions_dev_v2.csv")
    rapport["questions_dev_v2"] = {
        "questions": len(questions),
        "par_type": dict(Counter(l["type"] for l in questions)),
        "par_langue": dict(Counter(l["langue"] for l in questions)),
        "identifiants_dupliques": doublons(questions, "id"),
        "questions_dupliquees": doublons(questions, "question"),
        "hash_conforme_journal": sha256(RACINE / "data/dev/questions_dev_v2.csv")
        == EMPREINTES_RECUPEREES["data/dev/questions_dev_v2.csv"],
        "limite": "Jeu de développement uniquement ; aucune comparaison dev/test effectuée.",
    }
    notebook = json.loads((RACINE / "notebooks/01_data_exploration.ipynb").read_bytes())
    erreurs = []
    for i, cellule in enumerate(notebook["cells"]):
        if cellule["cell_type"] == "code":
            try:
                ast.parse("".join(cellule["source"]))
            except SyntaxError as erreur:
                erreurs.append({"cellule": i, "erreur": str(erreur)})
    rapport["notebook"] = {
        "cellules": len(notebook["cells"]),
        "cellules_code": sum(c["cell_type"] == "code" for c in notebook["cells"]),
        "erreurs_syntaxe": erreurs,
        "execute": False,
        "limite": "Analyse syntaxique seule ; les sorties enregistrées sont historiques.",
    }
    rapport["empreintes_entrees_complementaires"] = {
        nom: sha256(RACINE / "data/dev" / nom)
        for nom in ("alignement_dev_v1.csv", "alignement_dev_v2_a_annoter.csv",
                    "obligations_candidats_dev_v1.csv")
    }
    rapport["alignement_complet"] = auditer_alignement_complet()
    return rapport


if __name__ == "__main__":
    # ASCII JSON pour fonctionner aussi dans les terminaux Windows non UTF-8.
    print(json.dumps(auditer(), ensure_ascii=True, indent=2))
