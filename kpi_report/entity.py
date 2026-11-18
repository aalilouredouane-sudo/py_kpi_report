from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import RETURN_PERIODS, YELT_ROOT, ModeConfig
from .metrics import exceedance_table
from .reader import CatfileReader


class EntityReport:
    """Tableau des KPI (AEP, OEP, TVaR) de tous les catfiles d'une entité, côte à côte."""

    def __init__(self, root: Path, entity: str, simus: list[str],
                 mode: ModeConfig, n_years: int):
        self.root = root
        self.entity = entity
        self.simus = simus
        self.mode = mode
        self.n_years = n_years

    @property
    def code(self) -> str:
        return self.entity.replace("/", "")

    def _catfile_dir(self, simu: str) -> Path:
        folder = self.root / self.entity / simu / YELT_ROOT / self.mode.folder
        if self.mode.descend_first_dir:
            folder = sorted(folder.iterdir())[0]
        return folder

    def _catfiles(self, simu: str) -> list[Path]:
        return sorted(self._catfile_dir(simu).glob(self.mode.pattern))

    def _kpis(self) -> dict[str, pd.DataFrame]:
        """Table de KPI par catfile."""
        kpis = {}
        for simu in self.simus:
            for catfile_path in self._catfiles(simu):
                reader = CatfileReader(catfile_path, self.mode, self.n_years)
                kpis[reader.code] = exceedance_table(
                    reader.annual_losses(), reader.max_event_losses(), RETURN_PERIODS)
        return kpis

    @staticmethod
    def _combine(kpis: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Juxtapose les tables, séparées par une colonne vide."""
        if not kpis:
            return pd.DataFrame()
        dfs = []
        for df in kpis.values():
            dfs.append(df)
            separator = pd.DataFrame(index=df.index)
            separator[""] = ""
            dfs.append(separator)
        return pd.concat(dfs[:-1], axis=1)

    def build(self) -> pd.DataFrame:
        return self._combine(self._kpis())
