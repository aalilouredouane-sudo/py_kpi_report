from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from .config import YELT_ROOT, ModeConfig
from .entity import EntityReport
from .reader import loss_columns

logger = logging.getLogger(__name__)

GROUP_ENTITY = "GROUP"
GROUP_LOB_COL = "LOSS_LoB1"  # unique LoB du catfile GROUP (fullsize)
KEYS = ["YEAR", "EVENTID"]  # colonnes clés, dans l'ordre du catfile écrit
_SEED_SUFFIX = re.compile(r"^(?P<base>.+)_(?P<seed>\d+)$")


def seed_catfiles(files: list[Path]) -> dict[int, Path]:
    """Associe chaque catfile à son seed : 0 sans suffixe, x pour le suffixe `_x`.

    Un fichier n'est considéré comme suffixé que si le fichier sans suffixe existe
    dans le même dossier, pour ne pas confondre un nom finissant par `_<chiffres>`.
    """
    stems = {p.stem for p in files}
    by_seed: dict[int, Path] = {}
    for path in files:
        match = _SEED_SUFFIX.match(path.stem)
        seed = int(match["seed"]) if match and match["base"] in stems else 0
        if seed in by_seed:
            raise ValueError(
                f"Two catfiles map to seed {seed}: {by_seed[seed].name} and {path.name}. "
                f"Expected one catfile without suffix and the others with a suffix _x.")
        by_seed[seed] = path
    return dict(sorted(by_seed.items()))


class GroupBuilder:
    """Écrit les catfiles du GROUP : pour chaque seed, agrégation des catfiles des entités.

    Les pertes des entités sont empilées puis sommées par (YEAR, EVENTID) : l'AEP est
    la même qu'avec une simple concaténation, et un événement touchant plusieurs entités
    compte comme un seul événement pour l'OEP. Les colonnes de perte de chaque entité
    (ses LoBs en fullsize, voir `loss_columns`) sont d'abord sommées : le GROUP n'a
    qu'une LoB.
    """

    def __init__(self, root: Path, entities: list[str], simus: list[str],
                 mode: ModeConfig, downsized_subdir: str | None = None,
                 name: str = GROUP_ENTITY):
        self.root = root
        self.entities = entities
        self.simus = simus
        self.mode = mode
        self.downsized_subdir = downsized_subdir
        self.name = name
        if name in entities:
            raise ValueError(f"'{name}' is built from the entities: remove it from `entities`.")

    def build(self) -> list[Path]:
        written = []
        for simu in self.simus:
            written += self._build_simu(simu)
        return written

    def _build_simu(self, simu: str) -> list[Path]:
        reports = {e: EntityReport(self.root, e, [simu], self.mode, 0, self.downsized_subdir)
                   for e in self.entities}
        catfiles = {e: seed_catfiles(r._catfiles(simu)) for e, r in reports.items()}
        seeds = self._common_seeds(simu, catfiles)

        first = self.entities[0]
        out_dir = self._output_dir(simu, reports[first]._catfile_dir(simu))
        self._clear(out_dir)

        written = []
        for seed in seeds:
            print(f"  Merging {simu} seed {seed}")
            frames = [self._read(catfiles[e][seed]) for e in self.entities]
            merged = (pd.concat(frames, ignore_index=True)
                      .groupby(KEYS, as_index=False)["loss"].sum())
            out_path = out_dir / catfiles[first][seed].name.replace(first, self.name)
            self._to_catfile(merged).to_csv(out_path, index=False)
            written.append(out_path)
        return written

    def _common_seeds(self, simu: str, catfiles: dict[str, dict[int, Path]]) -> list[int]:
        """Erreur si les entités n'ont pas les mêmes seeds : un GROUP incomplet serait faux."""
        reference = set(catfiles[self.entities[0]])
        for entity, by_seed in catfiles.items():
            if set(by_seed) != reference:
                raise ValueError(
                    f"{simu}: seeds differ between entities "
                    f"({self.entities[0]}: {sorted(reference)}, {entity}: {sorted(by_seed)}).")
        return sorted(reference)

    def _output_dir(self, simu: str, entity_dir: Path) -> Path:
        """Même arborescence que les entités ; en downsized, même sous-dossier que la 1re entité."""
        folder = self.root / self.name / simu / YELT_ROOT / self.mode.folder
        if self.mode.descend_first_dir:
            folder = folder / entity_dir.name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _clear(self, folder: Path) -> None:
        """Supprime les catfiles d'un run précédent, pour ne pas mélanger d'anciens seeds."""
        for old in folder.glob(self.mode.pattern):
            old.unlink()

    def _read(self, path: Path) -> pd.DataFrame:
        """Pertes par ligne du catfile, toutes LoBs confondues : YEAR, EVENTID, loss."""
        loss_cols = loss_columns(path, self.mode)
        df = pd.read_csv(path, usecols=KEYS + loss_cols)
        return df[KEYS].assign(loss=df[loss_cols].sum(axis=1))

    def _to_catfile(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Colonnes du catfile GROUP, lisibles par `CatfileReader` comme celles d'une entité."""
        out = merged[KEYS].copy()
        if self.mode.lob_prefix:
            out[GROUP_LOB_COL] = merged["loss"]
        out[self.mode.loss_col] = merged["loss"]
        return out
