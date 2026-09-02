# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — level-0 physics benchmark

"""Benchmark the level-0 physics kernels: Python floor versus native.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per (operation, backend), unavailable backends marked
explicitly, full provenance in the artefact. The operation is the Bennett
equilibrium plus the Kadomtsev, shear and Pease-Braginskii evaluations
over a grid of synthetic parameter points; each sample times one full
grid pass. Nothing measured here is a physics claim.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scpn_z_pinch_core.parameters import Discharge, PinchColumn  # noqa: E402
from scpn_z_pinch_core.physics import (  # noqa: E402
    DEUTERON_MASS_KG,
    IDEAL_MONATOMIC_ADIABATIC_INDEX,
    bennett_equilibrium,
    kadomtsev_assessment,
    minimum_stabilising_shear,
    pease_braginskii_current,
)

SCHEMA: Final = "scpn-z-pinch-core.level0-physics-benchmark.v1"


def grid(points: int) -> list[tuple[float, float, float]]:
    """Build a deterministic synthetic parameter grid.

    Parameters
    ----------
    points
        Number of grid points.

    Returns
    -------
    list of (float, float, float)
        (column_radius_m, peak_current_ma, ion_line_density_per_m) tuples.
    """
    return [
        (
            5.0e-4 + 4.5e-3 * (index % 97) / 96.0,
            0.01 + 2.99 * (index % 89) / 88.0,
            1.0e17 * (1.0 + 999.0 * (index % 83) / 82.0),
        )
        for index in range(points)
    ]


def floor_pass(sample_grid: list[tuple[float, float, float]]) -> float:
    """Run one grid pass on the Python floor.

    Parameters
    ----------
    sample_grid
        Parameter grid.

    Returns
    -------
    float
        Checksum of the results, so the work cannot be optimised away.
    """
    total = 0.0
    for radius, current, density in sample_grid:
        equilibrium = bennett_equilibrium(
            PinchColumn(column_radius_m=radius, column_length_m=0.5),
            Discharge(peak_current_ma=current, ion_line_density_per_m=density),
            DEUTERON_MASS_KG,
        )
        total += equilibrium.alfven_speed_m_s
        total += kadomtsev_assessment(1.0, IDEAL_MONATOMIC_ADIABATIC_INDEX).threshold
        total += minimum_stabilising_shear(equilibrium, 200.0)
        total += pease_braginskii_current(10.0, 1.0)
    return total


def native_pass_factory() -> Callable[[list[tuple[float, float, float]]], float] | None:
    """Return the native grid pass when the native module is importable.

    Returns
    -------
    callable or None
        The pass function, or None when scpn_z_pinch_native is absent.
    """
    try:
        native = importlib.import_module("scpn_z_pinch_native")
    except ImportError:
        return None

    def native_pass(sample_grid: list[tuple[float, float, float]]) -> float:
        total = 0.0
        for radius, current, density in sample_grid:
            values = native.bennett_equilibrium(
                radius, current, density, DEUTERON_MASS_KG
            )
            total += values[5]
            total += native.kadomtsev_assessment(1.0, IDEAL_MONATOMIC_ADIABATIC_INDEX)[
                2
            ]
            total += native.minimum_stabilising_shear(values[5], 200.0)
            total += native.pease_braginskii_current(10.0, 1.0)
        return total

    return native_pass


def measure(
    run: Callable[[list[tuple[float, float, float]]], float],
    sample_grid: list[tuple[float, float, float]],
    warmup: int,
    repeats: int,
) -> dict[str, float]:
    """Time repeated grid passes and summarise them.

    Parameters
    ----------
    run
        Grid pass to time.
    sample_grid
        Parameter grid.
    warmup
        Discarded leading passes.
    repeats
        Timed passes.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min, max in microseconds per grid point and the
        throughput in points per second (P50-based).
    """
    for _ in range(warmup):
        run(sample_grid)
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        run(sample_grid)
        samples.append((time.perf_counter_ns() - start) / 1e3 / len(sample_grid))
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    p50 = percentile(0.5)
    return {
        "p50_us_per_point": p50,
        "p95_us_per_point": percentile(0.95),
        "p99_us_per_point": percentile(0.99),
        "mean_us_per_point": statistics.fmean(samples),
        "min_us_per_point": ordered[0],
        "max_us_per_point": ordered[-1],
        "throughput_points_per_s": 1e6 / p50,
    }


def provenance() -> dict[str, Any]:
    """Collect the environment provenance of a run.

    Returns
    -------
    dict[str, Any]
        Interpreter, platform, CPU model, commit and host-load context.
    """
    cpu_model = "unknown"
    with contextlib.suppress(OSError):
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    load = "unavailable"
    with contextlib.suppress(OSError):
        load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[0]
    commit = "unknown"
    git = shutil.which("git")
    if git is not None:
        with contextlib.suppress(OSError):
            commit = subprocess.run(
                [git, "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "load_average_1min_at_start": load,
        "commit": commit,
        "isolated_cores": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark command-line interface.

    Parameters
    ----------
    argv
        Argument vector; None reads sys.argv.

    Returns
    -------
    int
        0 on completion.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=100_000)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    sample_grid = grid(args.points)
    results: list[dict[str, Any]] = [
        {
            "name": "level0_grid_pass",
            "backend": "python_floor",
            "stats": measure(floor_pass, sample_grid, args.warmup, args.repeats),
            "status": "measured",
        }
    ]
    native_pass = native_pass_factory()
    if native_pass is None:
        results.append(
            {
                "name": "level0_grid_pass",
                "backend": "rust_native",
                "stats": None,
                "status": "unavailable: scpn_z_pinch_native not installed",
            }
        )
    else:
        stats = measure(native_pass, sample_grid, args.warmup, args.repeats)
        results.append(
            {
                "name": "level0_grid_pass",
                "backend": "rust_native",
                "stats": stats,
                "status": "measured",
                "requires": "optional native build (rust/, maturin)",
            }
        )
        floor_p50 = results[0]["stats"]["p50_us_per_point"]
        results[1]["speedup_p50_vs_python_floor"] = (
            floor_p50 / stats["p50_us_per_point"]
        )
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {
            "points": args.points,
            "warmup": args.warmup,
            "repeats": args.repeats,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"level0_physics.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['backend']}: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
