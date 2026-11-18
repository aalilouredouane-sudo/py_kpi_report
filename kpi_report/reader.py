from __future__ import annotations

from functools import cached_property
from pathlib import Path

import pandas as pd

from .config import ModeConfig


class CatfileReader:
    """Lit un catfile et construit ses stripfiles AEP et OEP."""

    def __init__(self, catfile_path: Path, mode: ModeConfig, n_years: int):
        self.catfile_path = catfile_path
        self.mode = mode
        self.n_years = n_years

    @property
    def code(self) -> str:
        return self.catfile_path.stem

    @property
    def years(self) -> pd.RangeIndex:
        return pd.RangeIndex(1, self.n_years + 1, name="year")

    @cached_property
    def event_losses(self) -> pd.DataFrame:
        """Pertes par événement : eventid, year, total."""
        print(f"  Reading {self.catfile_path}")
        df = pd.read_csv(self.catfile_path)
        df = df[["EVENTID", "YEAR", self.mode.loss_col]]
        return df.rename(columns={"EVENTID": "eventid", "YEAR": "year",
                                  self.mode.loss_col: "total"})

    def annual_losses(self) -> pd.Series:
        """Stripfile AEP : perte annuelle agrégée, années 1..n_years (0 si absente)."""
        return (self.event_losses.groupby("year")["total"].sum()
                .reindex(self.years, fill_value=0))

    def max_event_losses(self) -> pd.Series:
        """Stripfile OEP : plus grosse perte d'événement par année."""
        return (self.event_losses.groupby("year")["total"].max()
                .reindex(self.years, fill_value=0))
