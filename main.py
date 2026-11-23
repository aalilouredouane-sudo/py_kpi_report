import importlib.util
import subprocess
import sys
from pathlib import Path

# module importable -> spécification pip
REQUIREMENTS = {
    "numpy": "numpy>=1.24",
    "pandas": "pandas>=2.0",
    "openpyxl": "openpyxl>=3.1",
}


def ensure_dependencies() -> None:
    """Installe les packages manquants avant l'import du package kpi_report."""
    missing = [spec for mod, spec in REQUIREMENTS.items()
               if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


ensure_dependencies()

from kpi_report import KpiReportPipeline  # noqa: E402

if __name__ == "__main__":
    nbsimu = 1000000
    mode = "downsized"  # "fullsize" ou "downsized"

    KpiReportPipeline(
        root=Path("C:/Users/B497NP/OneDrive - AXA/Desktop/3. Terrorism and Conflagration/FY26/10. others/4. convergence/runs_CFHZ"),
        output_dir=Path("C:/Users/B497NP/OneDrive - AXA/Desktop/3. Terrorism and Conflagration/FY26/10. others/4. convergence/analysis"),
        entities=["CHE", "DEU", "FRA"],
        simus=[f"n{nbsimu}"],
        nbsimu=nbsimu,
        mode=mode,
        n_years=nbsimu if mode == "fullsize" else None,  # downsized : valeur de config.py (50 000)
        report_name="summary_CFHZ",
        downsized_subdir=None,  # sous-dossier de YELT_downsized_final ; None = le premier par ordre alphabétique
    ).run()
