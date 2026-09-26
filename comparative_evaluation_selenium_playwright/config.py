"""Locations and naming conventions of a measurement series.

A measurement series is stored in each framework repository under
``reports/runs/<run folder>/<run set>/<nn> <os>,<framework>,<browser>,headless-report``.
Results of a configuration are either directly in that folder (single session) or in
``session_01 ... session_NN`` subfolders. ``warmup`` subfolders and any ``superseded``
folder are excluded from the analysis.

Two settings come from environment variables, the same ones run_measurements.sh uses:

    RUN_FOLDER       measurement series under reports/runs/ (required)
    FRAMEWORKS_ROOT  folder that contains selenium-python-framework and playwright-python-framework
                     (default: the folder that contains this repository)
"""
import os
import sys
from pathlib import Path

ANALYZER_ROOT = Path(__file__).resolve().parents[1]

FRAMEWORKS_ROOT = Path(os.environ.get("FRAMEWORKS_ROOT") or ANALYZER_ROOT.parent)
FRAMEWORKS = ("selenium", "playwright")

RUN_FOLDER = os.environ.get("RUN_FOLDER")
if not RUN_FOLDER:
    sys.exit("Set RUN_FOLDER to the measurement series under reports/runs/, "
             "e.g. in PowerShell: $env:RUN_FOLDER = \"series_01\"")

# run set -> what it contains
RUN_SETS = {
    "10runs": "cross-browser execution time",
    "50runs": "repeated execution time (Chrome)",
    "50runs_resources": "resource utilization (Chrome)",
}

# Sampling interval of the resource monitor, needed to turn samples into CPU time
MONITOR_INTERVAL_S = 0.5

OUTPUT_DIR = ANALYZER_ROOT / "data" / "output"
PLOTS_DIR = ANALYZER_ROOT / "plots" / RUN_FOLDER


def repo_path(framework: str) -> Path:
    return FRAMEWORKS_ROOT / f"{framework}-python-framework"


def run_set_path(framework: str, run_set: str) -> Path:
    return repo_path(framework) / "reports" / "runs" / RUN_FOLDER / run_set
