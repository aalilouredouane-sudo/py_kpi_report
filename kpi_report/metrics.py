from __future__ import annotations

import numpy as np
import pandas as pd


def exceedance_table(annual: pd.Series, max_event: pd.Series, return_periods) -> pd.DataFrame:
    """AEP, OEP, TVaR_AEP et TVaR_OEP par période de retour.

    Pour chaque période de retour RP, k = ceil(n_years / RP) : l'AEP (OEP) est la
    k-ième plus grande valeur du stripfile, et la TVaR la moyenne des k plus grandes.
    """
    aep_sorted = np.sort(annual.to_numpy())
    oep_sorted = np.sort(max_event.to_numpy())
    n_years = len(aep_sorted)

    results = {"RP": [], "AEP": [], "OEP": [], "TVaR_AEP": [], "TVaR_OEP": []}
    for rp in return_periods:
        k = int(np.ceil(n_years / rp))
        results["RP"].append(rp)
        results["AEP"].append(aep_sorted[-k])
        results["OEP"].append(oep_sorted[-k])
        results["TVaR_AEP"].append(aep_sorted[-k:].mean())
        results["TVaR_OEP"].append(oep_sorted[-k:].mean())
    return pd.DataFrame(results)
