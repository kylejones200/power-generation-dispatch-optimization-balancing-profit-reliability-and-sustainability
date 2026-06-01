#!/usr/bin/env python3
"""Python vs Rust kernel benchmark."""

from __future__ import annotations

import time
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from compute_kernel import economic_dispatch_cost  # noqa: E402

def main() -> None:
    mw_demand = 200.0
    unit_mw = np.ascontiguousarray([100.0, 80.0, 60.0, 40.0])
    unit_cost = np.ascontiguousarray([25.0, 30.0, 45.0, 60.0])
    t0 = time.perf_counter()
    for _ in range(200):
        economic_dispatch_cost(mw_demand, unit_mw, unit_cost)
    py_s = time.perf_counter() - t0
    try:
        import power_generation_dispatch_optimization_balancing_profit_reliability_and_sustainability_rs as rs
    except ImportError:
        print("Build: maturin develop --release -m rust/py/Cargo.toml")
        print(f"Python {py_s:.3f}s")
        return
    rs_s = rs.bench_kernel_py(mw_demand, unit_mw, unit_cost, 50000)
    print(f"Python {py_s:.3f}s Rust {rs_s:.3f}s speedup {py_s / max(rs_s, 1e-9):.1f}x")
    np.testing.assert_allclose(
        economic_dispatch_cost(mw_demand, unit_mw, unit_cost),
        rs.economic_dispatch_cost_py(mw_demand, unit_mw, unit_cost),
        rtol=1e-10,
    )
    print("Correctness: OK")

if __name__ == "__main__":
    main()
