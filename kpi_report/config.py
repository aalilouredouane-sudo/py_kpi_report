from __future__ import annotations

from dataclasses import dataclass

RETURN_PERIODS = range(1, 2001)
YELT_ROOT = "YELT/YELT_Central"
NBSIMU_1M = 1000000  # nbsimu donnant le suffixe "_1m" dans le nom du rapport


@dataclass(frozen=True)
class ModeConfig:
    folder: str                      # sous-dossier de YELT_ROOT contenant les catfiles
    pattern: str                     # motif glob des catfiles
    loss_col: str                    # colonne de perte à lire
    n_years: int | None              # nombre d'années simulées ; None = nbsimu (donné dans main.py)
    descend_first_dir: bool = False  # descendre dans le premier sous-dossier trouvé
    suffix: str = ""                 # suffixe du nom du rapport
    lob_prefix: str | None = None    # préfixe des colonnes de perte par LoB, sommées pour le GROUP


MODES = {
    "fullsize": ModeConfig(
        folder="YELT_full_size",
        pattern="*YELT_full_size*.csv",
        loss_col="TOTAL_LOSS",
        n_years=None,  # une année par simulation : n_years = nbsimu
        lob_prefix="LOSS_",
    ),
    "downsized": ModeConfig(
        folder="YELT_downsized_final",
        pattern="f2*pool_property*.csv",
        loss_col="Loss",
        n_years=50000,
        descend_first_dir=True,
        suffix="_downsized",
    ),
}
