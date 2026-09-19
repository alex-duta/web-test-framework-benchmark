"""LaTeX tables for publication, built from the CSV files written by parse_reports.py.

The better (lower) value of each Selenium-Playwright comparison is set in bold when the
difference is significant (Mann-Whitney U, p < 0.05). Tables are written to data/output/.

Usage:  py src\\paper\\latex_tables.py
"""
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/, for config and compute_statistics

import config as cfg  # noqa: E402
from compute_statistics import load, describe, compare, magnitude, group  # noqa: E402

OS_LABEL = {"win": "Windows", "linux": "Linux"}
BROWSER_LABEL = {"chrome": "Chrome", "edge": "Edge", "firefox": "Firefox"}
FRAMEWORK_LABEL = {"selenium": "Selenium", "playwright": "Playwright"}


def fmt_p(p):
    return "$<0.001$" if p < 0.001 else f"{p:.3f}"


SIGNIFICANCE = 0.05
BOLD_NOTE = "Bold marks the lower (better) value of each Selenium--Playwright comparison."


def bold_lower(cells, values, p):
    """Bold the cell with the lower value, when the difference is significant."""
    cells = list(cells)
    if p < SIGNIFICANCE and values[0] != values[1]:
        better = 0 if values[0] < values[1] else 1
        cells[better] = "\\textbf{" + cells[better] + "}"
    return cells


def cross_browser_tables(rows):
    """Two tables: total execution time with effect size, and the phase breakdown."""
    grouped = group(rows, "10runs")
    total = [
        r"\begin{table}[htbp]",
        r"\caption{Execution time per suite repetition in the cross-browser data set (mean $\pm$ SD over ten repetitions, in seconds). " + BOLD_NOTE + "}",
        r"\label{tab:cross_browser}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{",
        r"\begin{tabular}{llrrrrr}",
        r"\hline",
        r"\textbf{OS} & \textbf{Browser} & \textbf{Selenium} & \textbf{Playwright} & \textbf{Ratio} & \textbf{$\hat{A}_{12}$} & \textbf{$p$} \\",
        r" & & \textbf{(mean $\pm$ SD)} & \textbf{(mean $\pm$ SD)} & & & \\",
        r"\hline",
    ]
    breakdown = [
        r"\begin{table}[htbp]",
        r"\caption{Decomposition of the execution time per suite repetition into test actions and test setup and teardown (cross-browser data set, mean in seconds). " + BOLD_NOTE + "}",
        r"\label{tab:cross_browser_phases}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{",
        r"\begin{tabular}{llrrrr}",
        r"\hline",
        r"\textbf{OS} & \textbf{Browser} & \multicolumn{2}{c}{\textbf{Test actions}} & \multicolumn{2}{c}{\textbf{Setup and teardown}} \\",
        r" & & \textbf{Selenium} & \textbf{Playwright} & \textbf{Selenium} & \textbf{Playwright} \\",
        r"\hline",
    ]
    print(f"\n{'CROSS-BROWSER (10 repetitions)':70}")
    print(f"{'os':6}{'browser':9}{'framework':11}{'total mean±sd':>18}{'call':>16}{'setup+teardown':>18}")
    for os_label in ("win", "linux"):
        for browser in ("chrome", "edge", "firefox"):
            stats_of = {}
            for framework in cfg.FRAMEWORKS:
                values = grouped.get((os_label, framework, browser), [])
                if not values:
                    continue
                stats_of[framework] = {metric: describe([v[metric] for v in values])
                                       for metric in ("total_s", "call_s", "setup_teardown_s")}
                d = stats_of[framework]
                print(f"{os_label:6}{browser:9}{framework:11}"
                      f"{d['total_s']['mean']:10.2f} ±{d['total_s']['sd']:5.2f}"
                      f"{d['call_s']['mean']:10.2f} ±{d['call_s']['sd']:4.2f}"
                      f"{d['setup_teardown_s']['mean']:11.2f} ±{d['setup_teardown_s']['sd']:4.2f}")
            if len(stats_of) != 2:
                continue
            sel = [v["total_s"] for v in grouped[(os_label, "selenium", browser)]]
            pw = [v["total_s"] for v in grouped[(os_label, "playwright", browser)]]
            p, effect = compare(sel, pw)
            ratio = st.mean(sel) / st.mean(pw)
            print(f"{'':26}Mann-Whitney p={fmt_p(p):>10}  A12={effect:.2f} ({magnitude(effect)})  ratio={ratio:.2f}")
            means = [stats_of[fw]["total_s"]["mean"] for fw in cfg.FRAMEWORKS]
            cells = bold_lower([f"{stats_of[fw]['total_s']['mean']:.1f} $\\pm$ {stats_of[fw]['total_s']['sd']:.1f}"
                                for fw in cfg.FRAMEWORKS], means, p)
            total.append(f"{OS_LABEL[os_label]} & {BROWSER_LABEL[browser]} & {cells[0]} & {cells[1]} & "
                         f"{ratio:.2f} & {effect:.2f} & {fmt_p(p)} \\\\")
            phase_cells = []
            for metric in ("call_s", "setup_teardown_s"):
                p_metric, _ = compare(*([v[metric] for v in grouped[(os_label, fw, browser)]] for fw in cfg.FRAMEWORKS))
                means = [stats_of[fw][metric]["mean"] for fw in cfg.FRAMEWORKS]
                phase_cells += bold_lower([f"{m:.1f}" for m in means], means, p_metric)
            breakdown.append(f"{OS_LABEL[os_label]} & {BROWSER_LABEL[browser]} & " + " & ".join(phase_cells) + " \\\\")
        total.append(r"\hline")
        breakdown.append(r"\hline")
    for lines in (total, breakdown):
        lines += [r"\end{tabular}", r"}", r"\end{table}"]
    return "\n".join(total), "\n".join(breakdown)


def repeated_execution(rows):
    """Console summary and LaTeX table for the Chrome 50-repetition data set."""
    grouped = group(rows, "50runs")
    print(f"\n{'REPEATED EXECUTION, CHROME (50 repetitions)':70}")
    lines = [
        r"\begin{table}[htbp]",
        r"\caption{Execution time per suite repetition in the repeated-execution data set (Chrome, 50 repetitions, in seconds). " + BOLD_NOTE + "}",
        r"\label{tab:repeated}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{",
        r"\begin{tabular}{llrrrrrr}",
        r"\hline",
        r"\textbf{OS} & \textbf{Framework} & \textbf{Mean} & \textbf{SD} & \textbf{Median} & \textbf{95\% CI} & \textbf{Test actions} & \textbf{Setup/teardown} \\",
        r"\hline",
    ]
    time_metrics = ("total_s", "call_s", "setup_teardown_s")
    for os_label in ("win", "linux"):
        samples, stats_of = {}, {}
        for framework in cfg.FRAMEWORKS:
            values = grouped[(os_label, framework, "chrome")]
            samples[framework] = {metric: [v[metric] for v in values] for metric in time_metrics}
            d = stats_of[framework] = {metric: describe(samples[framework][metric]) for metric in time_metrics}
            print(f"  {os_label:6}{framework:11} n={d['total_s']['n']:3} "
                  f"mean={d['total_s']['mean']:7.2f} sd={d['total_s']['sd']:5.2f} "
                  f"median={d['total_s']['median']:7.2f} "
                  f"CI=[{d['total_s']['ci_low']:.2f}, {d['total_s']['ci_high']:.2f}] "
                  f"call={d['call_s']['mean']:6.2f} setup+teardown={d['setup_teardown_s']['mean']:6.2f}")
        p_of = {metric: compare(samples["selenium"][metric], samples["playwright"][metric])[0]
                for metric in time_metrics}
        # the framework rows are compared column by column; mean and median follow the total-time test
        cells = {framework: {} for framework in cfg.FRAMEWORKS}
        for column, metric, stat in (("mean", "total_s", "mean"), ("median", "total_s", "median"),
                                     ("call", "call_s", "mean"), ("setup", "setup_teardown_s", "mean")):
            values = [stats_of[fw][metric][stat] for fw in cfg.FRAMEWORKS]
            for fw, cell in zip(cfg.FRAMEWORKS, bold_lower([f"{v:.2f}" for v in values], values, p_of[metric])):
                cells[fw][column] = cell
        for framework in cfg.FRAMEWORKS:
            d, c = stats_of[framework], cells[framework]
            lines.append(
                f"{OS_LABEL[os_label]} & {FRAMEWORK_LABEL[framework]} & "
                f"{c['mean']} & {d['total_s']['sd']:.2f} & {c['median']} & "
                f"{d['total_s']['ci_low']:.2f}--{d['total_s']['ci_high']:.2f} & "
                f"{c['call']} & {c['setup']} \\\\")
        p, effect = compare(samples["selenium"]["total_s"], samples["playwright"]["total_s"])
        ratio = st.mean(samples["selenium"]["total_s"]) / st.mean(samples["playwright"]["total_s"])
        print(f"  {'':17}Selenium/Playwright = {ratio:.2f}x, Mann-Whitney p={fmt_p(p)}, "
              f"A12={effect:.2f} ({magnitude(effect)})")
        lines.append(r"\hline")
    # environment effect per framework
    for framework in cfg.FRAMEWORKS:
        win = [v["total_s"] for v in grouped[("win", framework, "chrome")]]
        linux = [v["total_s"] for v in grouped[("linux", framework, "chrome")]]
        p, effect = compare(win, linux)
        change = (st.mean(linux) / st.mean(win) - 1) * 100
        print(f"  {framework:11} Windows -> Linux: {change:+.1f}%, p={fmt_p(p)}, A12={effect:.2f}")
    lines += [r"\end{tabular}", r"}", r"\end{table}"]
    return "\n".join(lines)


def resources(rows):
    """Console summary and LaTeX table for the resource data set."""
    grouped = group(rows, "50runs_resources")
    metrics = (("cpu_avg", "Average CPU (\\%)"), ("cpu_peak", "Peak CPU (\\%)"),
               ("mem_avg_mb", "Average memory (MB)"), ("mem_peak_mb", "Peak memory (MB)"))
    print(f"\n{'RESOURCE UTILIZATION, CHROME (50 repetitions)':70}")
    lines = [
        r"\begin{table}[htbp]",
        r"\caption{Resource utilization per suite repetition (Chrome, 50 repetitions, mean $\pm$ SD). Bold marks the lower (better) value of each Selenium--Playwright comparison; average CPU is not ranked, because it depends on the execution time.}",
        r"\label{tab:resources}",
        r"\centering",
        r"\resizebox{\columnwidth}{!}{",
        r"\begin{tabular}{llrrrr}",
        r"\hline",
        r"\textbf{OS} & \textbf{Metric} & \textbf{Selenium} & \textbf{Playwright} & \textbf{$\hat{A}_{12}$} & \textbf{$p$} \\",
        r"\hline",
    ]
    for os_label in ("win", "linux"):
        for metric, label in metrics:
            sel = [v[metric] for v in grouped[(os_label, "selenium", "chrome")]]
            pw = [v[metric] for v in grouped[(os_label, "playwright", "chrome")]]
            p, effect = compare(sel, pw)
            s, w = describe(sel), describe(pw)
            print(f"  {os_label:6}{label:20} sel {s['mean']:8.1f} ±{s['sd']:6.1f} | "
                  f"pw {w['mean']:8.1f} ±{w['sd']:6.1f} | ratio {s['mean']/w['mean']:.2f} "
                  f"p={fmt_p(p):>9} A12={effect:.2f} ({magnitude(effect)})")
            cells = [f"{s['mean']:.1f} $\\pm$ {s['sd']:.1f}", f"{w['mean']:.1f} $\\pm$ {w['sd']:.1f}"]
            if metric != "cpu_avg":  # a lower average over a longer run is not better
                cells = bold_lower(cells, [s["mean"], w["mean"]], p)
            lines.append(f"{OS_LABEL[os_label]} & {label} & {cells[0]} & {cells[1]} & {effect:.2f} & {fmt_p(p)} \\\\")
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"}", r"\end{table}"]
    return "\n".join(lines)


def main():
    rows = load("repetitions")
    resource_rows = load("resources")
    cross_total, cross_breakdown = cross_browser_tables(rows)
    tables = {
        "table_cross_browser.tex": cross_total,
        "table_cross_browser_phases.tex": cross_breakdown,
        "table_repeated.tex": repeated_execution(rows),
        "table_resources.tex": resources(resource_rows),
    }
    for name, content in tables.items():
        (cfg.OUTPUT_DIR / name).write_text(content + "\n", encoding="utf-8")
    print("\nLaTeX tables written to", cfg.OUTPUT_DIR)


if __name__ == "__main__":
    main()
