"""Read a measurement series into two tidy CSV files.

Outputs (in data/output/):
    <run folder>_repetitions.csv  one row per suite repetition: durations and outcome
    <run folder>_resources.csv    one row per suite repetition: CPU and memory

Usage:  py src\\parse_reports.py
"""
import csv
import json
import re
import statistics
from collections import defaultdict

import config as cfg

PHASES = ("setup", "call", "teardown")
REPETITION_RE = re.compile(r"(\d+)-\d+\]$")  # test id ends in -<repetition>-<count>]


def config_folders(framework, run_set):
    """Yield (os_label, browser, folder) for every configuration of a run set."""
    root = cfg.run_set_path(framework, run_set)
    if not root.is_dir():
        return
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        # "01 win,selenium,chrome,headless-report"
        parts = folder.name.split(",")
        os_label = parts[0].split()[1]
        browser = parts[2]
        yield os_label, browser, folder


def session_reports(folder):
    """Yield (session, report.json path); warm-up sessions are skipped."""
    if (folder / "report.json").is_file():
        yield 1, folder / "report.json"
    for session_dir in sorted(folder.glob("session_*")):
        report = session_dir / "report.json"
        if report.is_file():
            yield int(session_dir.name.split("_")[1]), report


def repetitions_of(report_path):
    """Return {repetition: {phase durations, outcome}} for one report."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reps = defaultdict(lambda: {"setup": 0.0, "call": 0.0, "teardown": 0.0, "tests": 0, "failed": 0})
    for test in report["tests"]:
        match = REPETITION_RE.search(test["nodeid"])
        key = int(match.group(1)) if match else 1
        rep = reps[key]
        rep["tests"] += 1
        if test["outcome"] != "passed":
            rep["failed"] += 1
        for phase in PHASES:
            rep[phase] += float(test.get(phase, {}).get("duration") or 0.0)
    return reps, report.get("browsers", [])


def resource_repetitions(samples_path):
    """Return {repetition: CPU and memory statistics} from a resource_samples.csv."""
    per_rep = defaultdict(list)
    with open(samples_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["repetition"]:  # samples before the first test are unlabeled
                per_rep[int(row["repetition"])].append(row)
    result = {}
    for key, rows in per_rep.items():
        cpu = [float(r["cpu_percent"]) for r in rows]
        mem = [float(r["mem_mb"]) for r in rows]
        result[key] = {
            "samples": len(rows),
            "cpu_avg": statistics.mean(cpu),
            "cpu_peak": max(cpu),
            "cpu_time_s": sum(cpu) / 100 * cfg.MONITOR_INTERVAL_S,
            "mem_avg_mb": statistics.mean(mem),
            "mem_peak_mb": max(mem),
            "processes_peak": max(int(r["processes"]) for r in rows),
        }
    return result


def main():
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    time_rows, resource_rows = [], []

    for run_set in cfg.RUN_SETS:
        for framework in cfg.FRAMEWORKS:
            for os_label, browser, folder in config_folders(framework, run_set):
                for session, report_path in session_reports(folder):
                    reps, browsers = repetitions_of(report_path)
                    for rep, values in sorted(reps.items()):
                        total = sum(values[p] for p in PHASES)
                        time_rows.append({
                            "run_set": run_set, "os": os_label, "framework": framework,
                            "browser": browser, "session": session, "repetition": rep,
                            "tests": values["tests"], "failed": values["failed"],
                            "complete": values["failed"] == 0,
                            "total_s": round(total, 4),
                            "call_s": round(values["call"], 4),
                            "setup_teardown_s": round(values["setup"] + values["teardown"], 4),
                            "browsers": "; ".join(browsers),
                        })
                    samples = report_path.parent / "resource_samples.csv"
                    if samples.is_file():
                        for rep, values in sorted(resource_repetitions(samples).items()):
                            resource_rows.append({
                                "run_set": run_set, "os": os_label, "framework": framework,
                                "browser": browser, "session": session, "repetition": rep,
                                "complete": reps[rep]["failed"] == 0,
                                **{k: round(v, 4) if isinstance(v, float) else v for k, v in values.items()},
                            })

    for name, rows in ((f"{cfg.RUN_FOLDER}_repetitions.csv", time_rows),
                       (f"{cfg.RUN_FOLDER}_resources.csv", resource_rows)):
        if not rows:
            continue
        path = cfg.OUTPUT_DIR / name
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"{path}: {len(rows)} rows")

    # short overview, so that mistakes in the folder layout are visible immediately
    seen = defaultdict(int)
    for row in time_rows:
        seen[(row["run_set"], row["os"], row["framework"], row["browser"])] += 1
    print("\nrepetitions per configuration")
    for key in sorted(seen):
        print(f"  {key[0]:17} {key[1]:5} {key[2]:11} {key[3]:8} {seen[key]:3}")
    incomplete = [r for r in time_rows if not r["complete"]]
    print(f"\nrepetitions containing a failed test: {len(incomplete)}")
    for row in incomplete:
        print(f"  {row['run_set']} {row['os']} {row['framework']} {row['browser']} "
              f"session {row['session']} repetition {row['repetition']} ({row['failed']} failed)")


if __name__ == "__main__":
    main()
