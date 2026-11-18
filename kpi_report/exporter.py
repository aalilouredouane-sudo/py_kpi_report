from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelExporter:
    """Écrit un classeur : une feuille par entité."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def export(self, tables: dict[str, pd.DataFrame]) -> None:
        with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
            for entity, table in tables.items():
                table.to_excel(writer, sheet_name=entity[:31], index=False)
