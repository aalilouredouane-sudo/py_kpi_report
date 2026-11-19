from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import RETURN_PERIODS, YELT_ROOT, ModeConfig
from .metrics import exceedance_table
from .reader import CatfileReader

logger = logging.getLogger(__name__)


@dataclass
class CatfileKpi:
    """Table de KPI d'un catfile, avec ce qu'il faut pour la tracer."""
    simu: str
    path: Path
    table: pd.DataFrame
    n_events: int
    last_year: int | None

    @property
    def label(self) -> str:
        return f"{self.simu} | {self.path.stem}"


class EntityReport:
    """Tables de KPI (AEP, OEP, TVaR) de tous les catfiles d'une entité."""

    def __init__(self, root: Path, entity: str, simus: list[str],
                 mode: ModeConfig, n_years: int, downsized_subdir: str | None = None):
        self.root = root
        self.entity = entity
        self.simus = simus
        self.mode = mode
        self.n_years = n_years
        self.downsized_subdir = downsized_subdir

    @property
    def code(self) -> str:
        return self.entity.replace("/", "")

    def _catfile_dir(self, simu: str) -> Path:
        folder = self.root / self.entity / simu / YELT_ROOT / self.mode.folder
        if not folder.is_dir():
            raise FileNotFoundError(f"Catfile folder not found: {folder}")
        if self.mode.descend_first_dir:
            folder = self._subdir(folder)
        return folder

    def _subdir(self, folder: Path) -> Path:
        """Sous-dossier imposé par `downsized_subdir`, sinon le premier par ordre alphabétique."""
        if self.downsized_subdir is not None:
            chosen = folder / self.downsized_subdir
            if not chosen.is_dir():
                raise FileNotFoundError(f"Subfolder not found: {chosen}")
            return chosen
        subdirs = sorted(p for p in folder.iterdir() if p.is_dir())
        if not subdirs:
            raise FileNotFoundError(f"No subfolder in {folder}")
        if len(subdirs) > 1:
            logger.warning(
                "%s contains %d subfolders (%s); using the first one: '%s'. "
                "Set `downsized_subdir` to choose another one.",
                folder, len(subdirs), ", ".join(p.name for p in subdirs), subdirs[0].name)
        return subdirs[0]

    def _catfiles(self, simu: str) -> list[Path]:
        folder = self._catfile_dir(simu)
        files = sorted(folder.glob(self.mode.pattern))
        if not files:
            raise FileNotFoundError(f"No catfile matching '{self.mode.pattern}' in {folder}")
        return files

    def build(self) -> list[CatfileKpi]:
        """Une table de KPI par catfile, dans l'ordre des simus puis des noms de fichiers."""
        kpis = []
        for simu in self.simus:
            for catfile_path in self._catfiles(simu):
                reader = CatfileReader(catfile_path, self.mode, self.n_years)
                table = exceedance_table(
                    reader.annual_losses(), reader.max_event_losses(), RETURN_PERIODS)
                kpis.append(CatfileKpi(simu, catfile_path, table,
                                       reader.n_events, reader.last_year))
        return kpis
