"""Statistics for a measurement series.

Reads the CSV files written by parse_reports.py and computes, for every comparison,
mean, SD, median, 95% CI, the Mann-Whitney U p-value and the Vargha-Delaney A12
effect size. Writes them to data/output/<run folder>_statistics.csv (see STATISTICS.md)
and prints a summary.

Usage:  py comparative_evaluation_selenium_playwright\\compute_statistics.py
"""
import csv
import statistics as st
from collections import defaultdict

from scipy.stats import mannwhitneyu, t as student_t

import config as cfg


def load(name):
    with open(cfg.OUTPUT_DIR / f"{cfg.RUN_FOLDER}_{name}.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key, value in row.items():
            if key not in ("run_set", "os", "framework", "browser", "browsers", "complete"):
                row[key] = float(value)
        row["complete"] = row["complete"] == "True"
    return rows


def describe(values):
    n = len(values)
    mean, sd = st.mean(values), st.stdev(values)
    half = student_t.ppf(0.975, n - 1) * sd / n ** 0.5
    return {"n": n, "mean": mean, "sd": sd, "median": st.median(values),
            "ci_low": mean - half, "ci_high": mean + half,
            "min": min(values), "max": max(values)}


def a12(first, second):
    """P(first > second) + 0.5 P(first == second): Vargha-Delaney effect size."""
    greater = sum((x > y) + 0.5 * (x == y) for x in first for y in second)
    return greater / (len(first) * len(second))


def compare(first, second):
    """Mann-Whitney U p-value and A12 for two samples."""
    p = mannwhitneyu(first, second, alternative="two-sided").pvalue
    return p, a12(first, second)


def magnitude(value):
    """Interpretation thresholds of A12 (Vargha and Delaney)."""
    distance = abs(value - 0.5)
    if distance < 0.06:
        return "negligible"
    if distance < 0.14:
        return "small"
    if distance < 0.21:
        return "medium"
    return "large"


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def group(rows, run_set, keys=("os", "framework", "browser")):
    out = defaultdict(list)
    for row in rows:
        if row["run_set"] == run_set and row["complete"]:
            out[tuple(row[k] for k in keys)].append(row)
    return out


def outcomes(rows):
    """Test executions and failures per framework, across the analysed run sets."""
    print(f"\n{'TEST OUTCOMES':70}")
    totals = defaultdict(lambda: [0, 0])
    for row in rows:
        if row["run_set"] in ("10runs", "50runs"):
            totals[row["framework"]][0] += int(row["tests"])
            totals[row["framework"]][1] += int(row["failed"])
    for framework, (tests, failed) in sorted(totals.items()):
        print(f"  {framework:11} {tests:5} test executions, {failed} failed "
              f"({100 * (tests - failed) / tests:.2f}% passed)")


STAT_FIELDS = ["n", "mean", "sd", "median", "ci_low", "ci_high", "min", "max"]


def comparison_row(data_set, metric, os_label, browser, comparison, name_a, values_a, name_b, values_b):
    """One CSV row: descriptive statistics of both groups and their comparison."""
    a, b = describe(values_a), describe(values_b)
    p, effect = compare(values_a, values_b)
    row = {"data_set": data_set, "metric": metric, "os": os_label, "browser": browser,
           "comparison": comparison, "group_a": name_a, "group_b": name_b}
    for prefix, stats in (("a", a), ("b", b)):
        for field in STAT_FIELDS:
            value = stats[field]
            row[f"{field}_{prefix}"] = value if field == "n" else round(value, 4)
    row["ratio_a_b"] = round(a["mean"] / b["mean"], 4)
    row["a12"] = round(effect, 4)
    row["a12_magnitude"] = magnitude(effect)
    row["p_value"] = f"{p:.3g}"
    return row


def statistics_rows(rows, resource_rows):
    """Every comparison of the measurement design, with all statistics."""
    out = []
    time_metrics = ("total_s", "call_s", "setup_teardown_s")

    grouped = group(rows, "10runs")
    for os_label in ("win", "linux"):
        for browser in ("chrome", "edge", "firefox"):
            for metric in time_metrics:
                sel = [v[metric] for v in grouped.get((os_label, "selenium", browser), [])]
                pw = [v[metric] for v in grouped.get((os_label, "playwright", browser), [])]
                if len(sel) > 1 and len(pw) > 1:
                    out.append(comparison_row("10runs", metric, os_label, browser, "framework",
                                              "selenium", sel, "playwright", pw))

    grouped = group(rows, "50runs")
    for metric in time_metrics:
        for os_label in ("win", "linux"):
            sel = [v[metric] for v in grouped[(os_label, "selenium", "chrome")]]
            pw = [v[metric] for v in grouped[(os_label, "playwright", "chrome")]]
            out.append(comparison_row("50runs", metric, os_label, "chrome", "framework",
                                      "selenium", sel, "playwright", pw))
        for framework in cfg.FRAMEWORKS:
            win = [v[metric] for v in grouped[("win", framework, "chrome")]]
            linux = [v[metric] for v in grouped[("linux", framework, "chrome")]]
            out.append(comparison_row("50runs", metric, "win vs linux", "chrome", f"environment ({framework})",
                                      "win", win, "linux", linux))

    grouped = group(resource_rows, "50runs_resources")
    for metric in ("cpu_avg", "cpu_peak", "cpu_time_s", "mem_avg_mb", "mem_peak_mb"):
        for os_label in ("win", "linux"):
            sel = [v[metric] for v in grouped[(os_label, "selenium", "chrome")]]
            pw = [v[metric] for v in grouped[(os_label, "playwright", "chrome")]]
            out.append(comparison_row("50runs_resources", metric, os_label, "chrome", "framework",
                                      "selenium", sel, "playwright", pw))
    return out


def write_statistics_csv(stats):
    path = cfg.OUTPUT_DIR / f"{cfg.RUN_FOLDER}_statistics.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(stats[0]))
        writer.writeheader()
        writer.writerows(stats)
    print(f"\nstatistics for {len(stats)} comparisons written to {path}")


def print_summary(stats):
    """One line per comparison, so the results can be checked without opening the CSV."""
    print(f"\n{'data set':18}{'metric':18}{'os':14}{'browser':9}{'group a':>12}{'group b':>12}"
          f"{'ratio':>8}{'A12':>6}{'p':>10}")
    for row in stats:
        print(f"{row['data_set']:18}{row['metric']:18}{row['os']:14}{row['browser']:9}"
              f"{row['mean_a']:12.2f}{row['mean_b']:12.2f}{row['ratio_a_b']:8.2f}{row['a12']:6.2f}"
              f"{fmt_p(float(row['p_value'])):>10}")


def main():
    rows = load("repetitions")
    resource_rows = load("resources")
    stats = statistics_rows(rows, resource_rows)
    print_summary(stats)
    outcomes(rows)
    write_statistics_csv(stats)


if __name__ == "__main__":
    main()
