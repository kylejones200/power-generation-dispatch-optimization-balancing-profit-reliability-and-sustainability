"""Merit-order economic dispatch total cost."""

from __future__ import annotations

import numpy as np


def economic_dispatch_cost(
    mw_demand: float, unit_mw: np.ndarray, unit_cost: np.ndarray
) -> float:
    mw = np.asarray(unit_mw, dtype=float)
    cost = np.asarray(unit_cost, dtype=float)
    remaining = float(mw_demand)
    total = 0.0
    order = np.argsort(cost)
    for idx in order:
        dispatch = max(0.0, min(remaining, mw[idx]))
        total += dispatch * cost[idx]
        remaining -= dispatch
        if remaining <= 1e-12:
            break
    return total
