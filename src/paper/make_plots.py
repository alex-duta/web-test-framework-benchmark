"""Figures for a measurement series, built from the CSV files written by parse_reports.py.

    1. repeated_execution_boxplot  suite time per repetition, Chrome, 50 repetitions
    2. resource_utilization        average CPU and average memory, Chrome, 50 repetitions

Usage:  py src\\paper\\make_plots.py
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/, for config

import matplotlib.pyplot as plt  # noqa: E402

import config as cfg  # noqa: E402
import plot_style as style  # noqa: E402

OS_LABEL = {"win": "Windows", "linux": "Linux"}
BROWSER_LABEL = {"chrome": "Chrome", "edge": "Edge", "firefox": "Firefox"}
NUMERIC = {"session", "repetition", "tests", "failed", "total_s", "call_s", "setup_teardown_s",
           "samples", "cpu_avg", "cpu_peak", "cpu_time_s", "mem_avg_mb", "mem_peak_mb", "processes_peak"}


def load(name):
    with open(cfg.OUTPUT_DIR / f"{cfg.RUN_FOLDER}_{name}.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["complete"] = row["complete"] == "True"
        for key in row:
            if key in NUMERIC:
                row[key] = float(row[key])
    return [row for row in rows if row["complete"]]


def by_config(rows, run_set, metric):
    values = defaultdict(list)
    for row in rows:
        if row["run_set"] == run_set:
            values[(row["os"], row["framework"], row["browser"])].append(row[metric])
    return values


def repeated_execution_boxplot(rows):
    """Distribution of the suite execution time over the 50 Chrome repetitions."""
    values = by_config(rows, "50runs", "total_s")
    order = [("win", "selenium"), ("win", "playwright"), ("linux", "selenium"), ("linux", "playwright")]
    data = [values[(os_label, fw, "chrome")] for os_label, fw in order]
    labels = [f"{OS_LABEL[os_label]}\n{fw.capitalize()}" for os_label, fw in order]

    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    box = ax.boxplot(data, tick_labels=labels, **style.BOX_KWARGS)
    for patch, (_, fw) in zip(box["boxes"], order):
        patch.set_facecolor(style.SELENIUM_FILL if fw == "selenium" else style.PLAYWRIGHT_FILL)
        patch.set_edgecolor("black")
    ax.set_ylabel("Suite execution time (s)")
    style.grid(ax)
    fig.tight_layout()
    style.save(fig, "repeated_execution_boxplot")


def resource_utilization(resource_rows):
    """Average CPU utilization and average memory over the 50 Chrome repetitions,
    stacked vertically so that the figure fits one column."""
    order = [("win", "selenium"), ("win", "playwright"), ("linux", "selenium"), ("linux", "playwright")]
    labels = [f"{OS_LABEL[os_label]}\n{fw.capitalize()}" for os_label, fw in order]

    fig, axes = plt.subplots(2, 1, figsize=(3.4, 4.4), sharex=True)
    for ax, metric, ylabel in ((axes[0], "cpu_avg", "Average CPU utilization (%)"),
                               (axes[1], "mem_avg_mb", "Average memory (MB)")):
        values = by_config(resource_rows, "50runs_resources", metric)
        data = [values[(os_label, fw, "chrome")] for os_label, fw in order]
        box = ax.boxplot(data, tick_labels=labels, **style.BOX_KWARGS)
        for patch, (_, fw) in zip(box["boxes"], order):
            patch.set_facecolor(style.SELENIUM_FILL if fw == "selenium" else style.PLAYWRIGHT_FILL)
            patch.set_edgecolor("black")
        ax.set_ylabel(ylabel)
        style.grid(ax)
    fig.tight_layout()
    style.save(fig, "resource_utilization")


def main():
    rows = load("repetitions")
    resource_rows = load("resources")
    print("figures:")
    repeated_execution_boxplot(rows)
    resource_utilization(resource_rows)


if __name__ == "__main__":
    main()
