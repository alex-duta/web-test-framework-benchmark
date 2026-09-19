"""Shared IEEE-oriented plot style and helpers for the figures."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import config as cfg  # noqa: E402

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "lines.linewidth": 1.0,
    "patch.linewidth": 0.5,
    "axes.edgecolor": "black",
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.5,
    "figure.dpi": 100,
})

# Greyscale fills, so the figures stay readable when printed in black and white
SELENIUM_FILL = "#bfbfbf"
PLAYWRIGHT_FILL = "#ffffff"
SECOND_FILL = "#7f7f7f"

BOX_KWARGS = dict(
    patch_artist=True,
    showfliers=True,
    medianprops={"color": "black", "linewidth": 1.0},
    whiskerprops={"color": "black", "linewidth": 0.5},
    capprops={"color": "black", "linewidth": 0.5},
    flierprops={"marker": "o", "markerfacecolor": "black", "markersize": 2.5, "alpha": 0.6},
)


def grid(ax):
    ax.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.6)
    ax.set_axisbelow(True)


def save(fig, name):
    """Save a figure as PDF (for the paper) and PNG (for quick viewing)."""
    cfg.PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png"):
        path = cfg.PLOTS_DIR / f"{name}.{suffix}"
        fig.savefig(path, dpi=300, bbox_inches="tight", format=suffix)
        print(f"  {path}")
    plt.close(fig)
