from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font

from .entity import CatfileKpi

PARAMETERS_SHEET = "Parameters"
BLOCK_WIDTH = 6  # 5 colonnes de KPI + 1 colonne vide de séparation


class ExcelExporter:
    """Écrit un classeur : une feuille par entité, plus une feuille de paramètres."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def export(self, tables: dict[str, list[CatfileKpi]],
               parameters: pd.DataFrame, files: pd.DataFrame) -> None:
        with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
            for entity, kpis in tables.items():
                self._write_entity(writer, entity[:31], kpis)
            parameters.to_excel(writer, sheet_name=PARAMETERS_SHEET, index=False)
            files.to_excel(writer, sheet_name=PARAMETERS_SHEET, index=False,
                           startrow=len(parameters) + 2)

    @staticmethod
    def _write_entity(writer: pd.ExcelWriter, sheet: str, kpis: list[CatfileKpi]) -> None:
        """Ligne 1 : nom du catfile ; ligne 2 : en-têtes ; puis une ligne par période de retour."""
        for j, kpi in enumerate(kpis):
            col = j * BLOCK_WIDTH
            kpi.table.to_excel(writer, sheet_name=sheet, startrow=1, startcol=col, index=False)
            cell = writer.sheets[sheet].cell(row=1, column=col + 1, value=kpi.label)
            cell.font = Font(bold=True)
