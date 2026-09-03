# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the axial-current pinch column with its azimuthal
field, the static-versus-sheared-flow class invariant, and the Bennett
temperature window the configuration model checks. The right-hand text
panel states only facts backed by the repository itself.

Outputs (written next to this script):

- ``repo_header.png`` — the pinch column between its electrodes with
  the axial current, azimuthal field and inward force (used by
  ``README.md``).
- ``repo_header_shear_classes.png`` — the static class beside the
  flow-stabilised class with its velocity profile.
- ``repo_header_bennett_window.png`` — the Bennett balance with the
  documented plasma window and flagged points.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, no random input).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"
RED = "#ff3366"
GREEN = "#3ddc84"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configurations", "z_pinch · sheared_flow_z_pinch"),
    ("Shear Invariant", "static = zero shear · sheared stabilised"),
    ("Reference", "Shumlak-Hartman, PRL 75 (1995) 3285"),
    ("Bennett Window", "temperature outside window flagged"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.74,
        "Z-PINCH CORE",
        color="white",
        fontsize=28,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.66,
        subtitle,
        color=CYAN,
        fontsize=11,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.615, 0.615], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.55
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def column_glow(
    ax: Any,
    centre_x: float,
    half_width: float,
    y_bottom: float,
    y_top: float,
    taper: float = 0.0,
) -> None:
    """Draw a vertical glowing plasma column."""
    grid_x = np.linspace(centre_x - 3.2 * half_width, centre_x + 3.2 * half_width, 160)
    grid_y = np.linspace(y_bottom, y_top, 200)
    mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)
    width = half_width * (
        1.0 - taper * np.abs(mesh_y - (y_bottom + y_top) / 2) / ((y_top - y_bottom) / 2)
    )
    rho = np.abs(mesh_x - centre_x) / width
    ax.contourf(
        mesh_x,
        mesh_y,
        np.exp(-rho * 1.8),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.85,
    )


def generate_pinch_column() -> None:
    """Generate ``repo_header.png``: the axial-current pinch column."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    for electrode_y, label in ((2.75, "anode"), (-2.75, "cathode")):
        ax.add_patch(
            plt.Rectangle(
                (3.4, electrode_y - 0.14),
                3.2,
                0.28,
                fill=False,
                ec=STEEL,
                lw=2.0,
                alpha=0.9,
            )
        )
        ax.text(
            6.85,
            electrode_y - 0.08,
            label,
            color="#667799",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.9,
        )

    column_glow(ax, 5.0, 0.5, -2.6, 2.6, taper=0.15)

    for arrow_y in (-1.7, -0.4, 0.9):
        ax.annotate(
            "",
            xy=(5.0, arrow_y + 0.85),
            xytext=(5.0, arrow_y),
            arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.4, "alpha": 0.7},
        )
    ax.text(
        5.22,
        1.9,
        "I (axial)",
        color="white",
        fontsize=8.5,
        fontfamily="monospace",
        alpha=0.85,
    )

    theta = np.linspace(0.0, 2.0 * np.pi, 200)
    for ring_y in (-1.9, -0.95, 0.0, 0.95, 1.9):
        ax.plot(
            5.0 + 1.05 * np.cos(theta),
            ring_y + 0.22 * np.sin(theta),
            color=CYAN,
            lw=1.3,
            alpha=0.75,
        )
        ax.annotate(
            "",
            xy=(5.0 + 1.05, ring_y + 0.02),
            xytext=(5.0 + 1.05, ring_y - 0.02),
            arrowprops={"arrowstyle": "->", "color": CYAN, "lw": 1.0, "alpha": 0.8},
        )
    ax.text(
        6.25,
        0.55,
        "B_θ",
        color=CYAN,
        fontsize=9,
        fontfamily="monospace",
        alpha=0.95,
    )

    for start_x, sign in ((3.6, +1), (6.4, -1)):
        for force_y in (-1.2, 0.5):
            ax.annotate(
                "",
                xy=(5.0 - sign * 0.75, force_y),
                xytext=(start_x, force_y),
                arrowprops={
                    "arrowstyle": "->",
                    "color": MAGENTA,
                    "lw": 1.3,
                    "alpha": 0.8,
                },
            )
    ax.text(
        3.35,
        -0.05,
        r"$J \times B$",
        color=MAGENTA,
        fontsize=9,
        fontfamily="monospace",
        ha="right",
        alpha=0.95,
    )

    ax.text(
        5.0,
        -3.0,
        "the current is the confinement · axial discharge, azimuthal field",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "The Current Is The Confinement")
    _save(fig, plt, "repo_header.png")


def generate_shear_classes() -> None:
    """Generate ``repo_header_shear_classes.png``: the class split."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    axial = np.linspace(-2.3, 2.3, 300)
    ripple = 0.42 + 0.10 * np.sin(4.2 * axial)
    grid_x = np.linspace(0.9, 3.9, 120)
    mesh_x, mesh_y = np.meshgrid(grid_x, axial)
    rho = np.abs(mesh_x - 2.4) / (0.42 + 0.10 * np.sin(4.2 * mesh_y))
    ax.contourf(
        mesh_x,
        mesh_y,
        np.exp(-rho * 1.8),
        levels=24,
        cmap=_glow_cmap(),
        alpha=0.8,
    )
    ax.plot(2.4 - ripple, axial, color=CYAN, lw=1.4, alpha=0.85)
    ax.plot(2.4 + ripple, axial, color=CYAN, lw=1.4, alpha=0.85)
    ax.text(
        2.4,
        2.7,
        "z_pinch · zero shear declared",
        color="#99bbdd",
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        2.4,
        -2.75,
        "static class · m=0 ripple illustrated",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )

    column_glow(ax, 7.4, 0.42, -2.3, 2.3)
    ax.plot([7.0, 7.0], [-2.3, 2.3], color=CYAN, lw=1.4, alpha=0.85)
    ax.plot([7.8, 7.8], [-2.3, 2.3], color=CYAN, lw=1.4, alpha=0.85)
    profile = ((7.08, 0.55), (7.22, 0.85), (7.4, 1.15), (7.58, 0.85), (7.72, 0.55))
    for arrow_x, length in profile:
        ax.annotate(
            "",
            xy=(arrow_x, 0.2 + length),
            xytext=(arrow_x, 0.2),
            arrowprops={"arrowstyle": "->", "color": GREEN, "lw": 1.2, "alpha": 0.85},
        )
    ax.text(
        7.4,
        1.75,
        "v_z(r) · sheared axial flow",
        color=GREEN,
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        7.4,
        2.7,
        "sheared_flow_z_pinch · stabilised",
        color="#99bbdd",
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        7.4,
        -2.75,
        "Shumlak-Hartman, PRL 75 (1995) 3285",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )

    ax.plot([5.0, 5.0], [-2.5, 2.5], color=STEEL, lw=0.8, alpha=0.4)
    _text_panel(fig, "Two Classes Split By Flow Shear")
    _save(fig, plt, "repo_header_shear_classes.png")


def generate_bennett_window() -> None:
    """Generate ``repo_header_bennett_window.png``: the checked window."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    ax.plot([1.0, 9.2], [1.7, 1.7], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([1.0, 1.0], [1.7, 9.1], color=STEEL, lw=1.0, alpha=0.7)
    ax.text(
        8.85,
        1.25,
        "pinch current I",
        color="#8899bb",
        fontsize=9.5,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(
        1.15,
        8.85,
        "Bennett T",
        color="#8899bb",
        fontsize=9.5,
        fontfamily="monospace",
    )

    current = np.linspace(0.0, 1.0, 300)
    px = 1.0 + 8.0 * current
    py = 1.7 + 6.9 * current**2
    ax.plot(px, py, color=CYAN, lw=2.6, alpha=0.95)
    ax.fill_between(px, py, 1.7, color=CYAN, alpha=0.05)
    ax.text(
        6.0,
        7.6,
        "T ∝ I² / N",
        color=CYAN,
        fontsize=10,
        fontfamily="monospace",
        alpha=0.95,
    )

    y_low = 1.7 + 6.9 * 0.25
    y_high = 1.7 + 6.9 * 0.65
    ax.fill_between([1.0, 9.0], y_low, y_high, color=GREEN, alpha=0.07)
    for level in (y_low, y_high):
        ax.plot(
            [1.0, 9.0],
            [level, level],
            color=GREEN,
            lw=1.0,
            alpha=0.6,
            ls=(0, (5, 3)),
        )
    ax.text(
        1.25,
        (y_low + y_high) / 2,
        "documented plasma window",
        color=GREEN,
        fontsize=8,
        fontfamily="monospace",
        va="center",
        alpha=0.9,
    )

    points = ((0.60, True), (0.88, False), (0.30, False))
    for fraction, inside in points:
        mark_x = 1.0 + 8.0 * fraction
        mark_y = 1.7 + 6.9 * fraction**2
        if inside:
            ax.plot(mark_x, mark_y, "o", color=GREEN, ms=7, alpha=0.95)
        else:
            ax.plot(
                mark_x,
                mark_y,
                "x",
                color=RED,
                ms=9,
                mew=2.2,
                alpha=0.95,
            )
    ax.text(
        7.55,
        7.35,
        "flagged",
        color=RED,
        fontsize=8,
        fontfamily="monospace",
        ha="right",
        alpha=0.9,
    )

    ax.text(
        5.0,
        0.75,
        "declared Bennett temperature checked against the documented window",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Pinch Balance Inside A Checked Window")
    _save(fig, plt, "repo_header_bennett_window.png")


if __name__ == "__main__":
    generate_pinch_column()
    generate_shear_classes()
    generate_bennett_window()
