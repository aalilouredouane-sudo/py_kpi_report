"""Construit le dossier GROUP : agrégation, seed par seed, des catfiles des entités.

À lancer avant main.py. Le dossier GROUP a la même arborescence qu'une entité :
pour en faire une feuille du rapport, ajouter "GROUP" à `entities` dans main.py.
"""
from pathlib import Path

from main import ensure_dependencies

ensure_dependencies()

from kpi_report.config import MODES  # noqa: E402
from kpi_report.group import GroupBuilder  # noqa: E402

if __name__ == "__main__":
    root = Path("C:/Users/B497NP/OneDrive - AXA/Desktop/3. Terrorism and Conflagration/FY26/10. others/4. convergence/runs_CFHZ")
    entities = ["CHE", "DEU", "FRA"]
    simus = ["n500000", "n1000000"]
    modes = ["fullsize", "downsized"]  # catfiles à agréger
    group_name = "GROUP"
    downsized_subdir = None  # sous-dossier de YELT_downsized_final ; None = le premier par ordre alphabétique

    for mode in modes:
        print(f"Start merging {mode} catfiles into {group_name}")
        written = GroupBuilder(root, entities, simus, MODES[mode],
                               downsized_subdir, group_name).build()
        print(f"Finish {mode}: {len(written)} catfiles written")
