from __future__ import annotations

from pathlib import Path

from .config import MODES, NBSIMU_1M
from .entity import EntityReport
from .exporter import ExcelExporter


class KpiReportPipeline:
    def __init__(self, root: Path, output_dir: Path, entities: list[str],
                 simus: list[str], nbsimu: int, mode: str = "downsized",
                 report_name: str = "summary_CFHZ", n_years: int | None = None):
        self.root = root
        self.output_dir = output_dir
        self.entities = entities
        self.simus = simus
        self.nbsimu = nbsimu
        self.mode = MODES[mode]
        self.report_name = report_name
        self.n_years = n_years or self.mode.n_years

    @property
    def output_path(self) -> Path:
        tag = "_1m" if self.nbsimu == NBSIMU_1M else ""
        return self.output_dir / f"{self.report_name}{tag}{self.mode.suffix}.xlsx"

    def run(self) -> None:
        tables = {}
        for entity in self.entities:
            print(f"Start for {entity}")
            report = EntityReport(self.root, entity, self.simus, self.mode, self.n_years)
            tables[report.code] = report.build()
            print(f"Finish for {entity}")
        ExcelExporter(self.output_path).export(tables)
        print(f"Excel file created: {self.output_path}")
