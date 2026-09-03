# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device CAD model benchmark

"""Benchmark the device CAD model: B-rep build, STEP export, faceting.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per (operation, backend), unavailable backends marked
explicitly, full provenance in the artefact. The operations are, on the
synthetic six-body device assembly: building the B-rep bodies with the
assembly manifest, exporting the normalised STEP bytes, faceting all
bodies into closed meshes, and one full ``build_device_cad`` record pass;
each sample times one operation and the cost is reported per operation.
The back-end is the pinned third-party kernel (``cadquery_ocp``); there is
no Python-floor row because the CAD kernels have no bit-exact floor by
design (the library's ADR 0006). Nothing measured here is a physics or
engineering claim.
"""

from __future__ import annotations

import argparse
import contextlib
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

from scpn_reactor_kernels.errors import CadUnavailableError  # noqa: E402

from scpn_z_pinch_core.configuration import (  # noqa: E402
    DeviceConfiguration,
    RegistryBinding,
)
from scpn_z_pinch_core.geometry import DeviceGeometry  # noqa: E402
from scpn_z_pinch_core.parameters import Discharge, PinchColumn  # noqa: E402

SCHEMA: Final = "scpn-z-pinch-core.device-model-cad-benchmark.v1"
REGISTRY_DIGEST: Final = (
    "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
)


def synthetic_design() -> tuple[DeviceConfiguration, DeviceGeometry]:
    """Build the synthetic configuration and geometry of the benchmark.

    Returns
    -------
    (DeviceConfiguration, DeviceGeometry)
        Synthetic values; nothing describes a real machine.
    """
    configuration = DeviceConfiguration(
        identifier="sheared_flow_z_pinch",
        column=PinchColumn(column_radius_m=0.01, column_length_m=0.5),
        discharge=Discharge(peak_current_ma=0.5, ion_line_density_per_m=1.0e18),
        flow_shear_per_s=1.0e7,
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )
    geometry = DeviceGeometry(
        inner_electrode_radius_m=0.05,
        outer_electrode_inner_radius_m=0.1,
        outer_electrode_wall_thickness_m=0.01,
        acceleration_region_length_m=1.0,
        assembly_region_length_m=0.6,
        chamber_inner_radius_m=0.15,
        chamber_wall_thickness_m=0.01,
        end_wall_thickness_m=0.02,
    )
    return configuration, geometry


def operations() -> list[tuple[str, Callable[[], float]]]:
    """Build the timed operations on the synthetic device assembly.

    Returns
    -------
    list of (name, callable)
        Each callable performs one operation and returns a checksum.

    Raises
    ------
    CadUnavailableError
        If the CAD back-end is absent.
    """
    from scpn_reactor_kernels.cad import (
        BrepAssembly,
        annular_tube_brep,
        cylinder_solid_brep,
        facet_assembly,
    )
    from scpn_reactor_kernels.cad import (
        step_bytes as library_step_bytes,
    )

    from scpn_z_pinch_core.geometry import build_device_cad
    from scpn_z_pinch_core.geometry.cad import (
        CAD_MODEL_NON_CLAIMS,
        CAD_MODEL_SCHEMA,
        CAD_MODEL_SCHEMA_VERSION,
    )
    from scpn_z_pinch_core.geometry.model import (
        BODY_CHAMBER_WALL,
        BODY_END_WALL_DOWNSTREAM,
        BODY_END_WALL_UPSTREAM,
        BODY_INNER_ELECTRODE,
        BODY_OUTER_ELECTRODE,
        BODY_PLASMA_COLUMN,
        MATERIAL_CHAMBER_WALL,
        MATERIAL_ELECTRODE_CONDUCTOR,
        MATERIAL_PLASMA,
        MODEL_UNITS,
        ROLE_ELECTRODE,
        ROLE_PLASMA,
        ROLE_VACUUM_BOUNDARY,
    )

    configuration, geometry = synthetic_design()
    column = configuration.column
    z_electrode_end = geometry.acceleration_region_length_m
    z_device_end = geometry.device_length_m

    def build() -> BrepAssembly:
        return BrepAssembly(
            (
                cylinder_solid_brep(
                    geometry.inner_electrode_radius_m,
                    0.0,
                    z_electrode_end,
                    BODY_INNER_ELECTRODE,
                    ROLE_ELECTRODE,
                    MATERIAL_ELECTRODE_CONDUCTOR,
                ),
                annular_tube_brep(
                    geometry.outer_electrode_inner_radius_m,
                    geometry.outer_electrode_outer_radius_m,
                    0.0,
                    z_device_end,
                    BODY_OUTER_ELECTRODE,
                    ROLE_ELECTRODE,
                    MATERIAL_ELECTRODE_CONDUCTOR,
                ),
                annular_tube_brep(
                    geometry.chamber_inner_radius_m,
                    geometry.chamber_outer_radius_m,
                    0.0,
                    z_device_end,
                    BODY_CHAMBER_WALL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    geometry.chamber_outer_radius_m,
                    0.0 - geometry.end_wall_thickness_m,
                    0.0,
                    BODY_END_WALL_UPSTREAM,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    geometry.chamber_outer_radius_m,
                    z_device_end,
                    z_device_end + geometry.end_wall_thickness_m,
                    BODY_END_WALL_DOWNSTREAM,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    column.column_radius_m,
                    z_electrode_end,
                    z_electrode_end + column.column_length_m,
                    BODY_PLASMA_COLUMN,
                    ROLE_PLASMA,
                    MATERIAL_PLASMA,
                ),
            )
        )

    def build_timed() -> float:
        return float(len(build().manifest_sha256()))

    assembly = build()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
    }

    def export() -> float:
        return float(len(library_step_bytes(assembly, extras)))

    def facet() -> float:
        meshes = facet_assembly(assembly, 1.0e-4, 0.1)
        return sum(mesh.signed_volume_m3() for mesh in meshes)

    def record() -> float:
        model = build_device_cad(configuration, geometry)
        return float(len(model.digest_sha256()))

    return [
        ("brep_build_and_manifest", build_timed),
        ("step_export_normalised", export),
        ("facet_six_bodies", facet),
        ("device_cad_record_build", record),
    ]


def measure(run: Callable[[], float], warmup: int, repeats: int) -> dict[str, float]:
    """Time repeated operations and summarise them.

    Parameters
    ----------
    run
        Operation to time.
    warmup
        Discarded leading runs.
    repeats
        Timed runs.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min, max in milliseconds per operation and the
        throughput in operations per second (P50-based).
    """
    for _ in range(warmup):
        run()
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        run()
        samples.append((time.perf_counter_ns() - start) / 1e6)
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    p50 = percentile(0.5)
    return {
        "p50_ms_per_operation": p50,
        "p95_ms_per_operation": percentile(0.95),
        "p99_ms_per_operation": percentile(0.99),
        "mean_ms_per_operation": statistics.fmean(samples),
        "min_ms_per_operation": ordered[0],
        "max_ms_per_operation": ordered[-1],
        "throughput_operations_per_s": 1e3 / p50,
    }


def provenance() -> dict[str, Any]:
    """Collect the environment provenance of a run.

    Returns
    -------
    dict[str, Any]
        Interpreter, platform, CPU model, commit, host load and back-end
        versions.
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
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    results: list[dict[str, Any]] = []
    try:
        timed = operations()
    except CadUnavailableError as exc:
        for name in (
            "brep_build_and_manifest",
            "step_export_normalised",
            "facet_six_bodies",
            "device_cad_record_build",
        ):
            results.append(
                {
                    "name": name,
                    "backend": "cadquery_ocp",
                    "stats": None,
                    "status": f"unavailable: {exc}",
                }
            )
    else:
        for name, run in timed:
            results.append(
                {
                    "name": name,
                    "backend": "cadquery_ocp",
                    "stats": measure(run, args.warmup, args.repeats),
                    "status": "measured",
                    "requires": "optional extra scpn-reactor-kernels[cad]",
                }
            )
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {
            "warmup": args.warmup,
            "repeats": args.repeats,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"device_model_cad.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['name']} [{row['backend']}]: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
