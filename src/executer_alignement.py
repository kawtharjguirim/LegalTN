"""Exécute le notebook d'alignement v6 localement, sans serveur Jupyter.

Les données sont lues dans data/processed. --sortie permet une nouvelle
exécution dans un dossier distinct ; les exports existants ne sont pas écrasés.
"""

import argparse
import json
import os
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sortie", type=Path, default=RACINE / "data/processed",
        help="Dossier de destination des trois exports v6.",
    )
    args = parser.parse_args()
    sortie = args.sortie.resolve()
    notebook = RACINE / "notebooks/03_alignement_fr_ar_v6.ipynb"
    cellules = json.loads(notebook.read_bytes())["cells"]
    # Le notebook utilise explicitement cette racine pour charger les corpus.
    os.environ["LEGALTN_ROOT"] = str(RACINE)
    espace = {"__name__": "__main__"}
    for numero, cellule in enumerate(cellules):
        if cellule["cell_type"] != "code":
            continue
        if numero == 5:
            # Sépare le dossier d'export du dossier contenant les entrées.
            sortie.mkdir(parents=True, exist_ok=True)
            espace["OUT_DIR"] = sortie
        source = "".join(cellule["source"])
        exec(compile(source, f"{notebook}:cellule{numero}", "exec"), espace)


if __name__ == "__main__":
    main()
