from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path

import pandas as pd

from .config import ModeConfig

logger = logging.getLogger(__name__)


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

    @property
    def columns(self) -> list[str]:
        return ["EVENTID", "YEAR", self.mode.loss_col]

    @cached_property
    def event_losses(self) -> pd.DataFrame:
        """Pertes par événement : eventid, year, total."""
        print(f"  Reading {self.catfile_path}")
        self._check_columns()
        df = pd.read_csv(self.catfile_path, usecols=self.columns)[self.columns]
        df = df.rename(columns={"EVENTID": "eventid", "YEAR": "year",
                                self.mode.loss_col: "total"})
        self._check_years(df["year"])
        return df

    def _check_columns(self) -> None:
        found = list(pd.read_csv(self.catfile_path, nrows=0).columns)
        missing = [c for c in self.columns if c not in found]
        if missing:
            raise ValueError(
                f"{self.catfile_path}: missing column(s) {missing}. "
                f"Expected {self.columns}, found {found}.")

    def _check_years(self, years: pd.Series) -> None:
        """Erreur si une année sort de 1..n_years ; alerte si les années s'arrêtent bien avant."""
        if years.empty:
            logger.warning("%s: no event in the catfile.", self.catfile_path)
            return
        first, last = years.min(), years.max()
        if first < 1 or last > self.n_years:
            raise ValueError(
                f"{self.catfile_path}: years range from {first} to {last}, outside "
                f"1..{self.n_years}. Check `n_years` (number of simulated years).")
        if last <= self.n_years // 2:
            logger.warning(
                "%s: last year with an event is %s, far below n_years = %s. "
                "Check `n_years` (number of simulated years).",
                self.catfile_path, last, self.n_years)

    @property
    def n_events(self) -> int:
        return len(self.event_losses)

    @property
    def last_year(self) -> int | None:
        years = self.event_losses["year"]
        return None if years.empty else int(years.max())

    def annual_losses(self) -> pd.Series:
        """Stripfile AEP : perte annuelle agrégée, années 1..n_years (0 si absente)."""
        return (self.event_losses.groupby("year")["total"].sum()
                .reindex(self.years, fill_value=0))

    def max_event_losses(self) -> pd.Series:
        """Stripfile OEP : plus grosse perte d'événement par année."""
        return (self.event_losses.groupby("year")["total"].max()
                .reindex(self.years, fill_value=0))
