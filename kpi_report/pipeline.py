from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import MODES, NBSIMU_1M
from .entity import CatfileKpi, EntityReport
from .exporter import PARAMETERS_SHEET, ExcelExporter

logger = logging.getLogger(__name__)


class KpiReportPipeline:
    def __init__(self, root: Path, output_dir: Path, entities: list[str],
                 simus: list[str], nbsimu: int, mode: str = "downsized",
                 report_name: str = "summary_CFHZ", n_years: int | None = None,
                 downsized_subdir: str | None = None):
        self.root = root
        self.output_dir = output_dir
        self.entities = entities
        self.simus = simus
        self.nbsimu = nbsimu
        self.mode_name = mode
        self.mode = MODES[mode]
        self.report_name = report_name
        self.n_years = n_years or self.mode.n_years or nbsimu
        self.downsized_subdir = downsized_subdir
        self._check_parameters()

    def _check_parameters(self) -> None:
        codes = [e.replace("/", "")[:31] for e in self.entities]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Several entities give the same sheet name: {duplicates}")
        if PARAMETERS_SHEET in codes:
            raise ValueError(f"'{PARAMETERS_SHEET}' is reserved for the parameters sheet")
        if self.mode_name == "fullsize" and self.n_years != self.nbsimu:
            logger.warning(
                "fullsize mode: n_years = %s but nbsimu = %s. "
                "Check that n_years matches the number of years in the catfiles.",
                self.n_years, self.nbsimu)

    @property
    def output_path(self) -> Path:
        tag = "_1m" if self.nbsimu == NBSIMU_1M else ""
        return self.output_dir / f"{self.report_name}{tag}{self.mode.suffix}.xlsx"

    def run(self) -> None:
        tables: dict[str, list[CatfileKpi]] = {}
        for entity in self.entities:
            print(f"Start for {entity}")
            report = EntityReport(self.root, entity, self.simus, self.mode,
                                  self.n_years, self.downsized_subdir)
            tables[report.code] = report.build()
            print(f"Finish for {entity}")
        ExcelExporter(self.output_path).export(
            tables, self._parameters_table(), self._files_table(tables))
        print(f"Excel file created: {self.output_path}")

    def _parameters_table(self) -> pd.DataFrame:
        rows = {
            "run_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "root": str(self.root),
            "output_file": str(self.output_path),
            "mode": self.mode_name,
            "n_years": self.n_years,
            "nbsimu": self.nbsimu,
            "entities": ", ".join(self.entities),
            "simus": ", ".join(self.simus),
            "downsized_subdir": self.downsized_subdir or "",
        }
        return pd.DataFrame({"Parameter": list(rows), "Value": [str(v) for v in rows.values()]})

    @staticmethod
    def _files_table(tables: dict[str, list[CatfileKpi]]) -> pd.DataFrame:
        return pd.DataFrame([
            {"entity": entity, "simu": k.simu, "catfile": k.path.name,
             "n_events": k.n_events, "last_year": k.last_year, "path": str(k.path)}
            for entity, kpis in tables.items() for k in kpis
        ])
