import argparse
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# IEEE-compliant matplotlib configuration
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "lines.linewidth": 1.0,
    "patch.linewidth": 0.5,
    "figure.figsize": (6.5, 4.5),
    "axes.edgecolor": "black",
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.5,
    "figure.dpi": 100,
})


def find_resource_csvs(root_dir):
    """Find all resource_summary.csv files in 10runs directories."""
    csv_files = []
    for entry in sorted(os.listdir(root_dir)):
        dir_path = os.path.join(root_dir, entry)
        csv_file = os.path.join(dir_path, "resource_summary.csv")
        if os.path.isdir(dir_path) and os.path.isfile(csv_file):
            csv_files.append((entry, csv_file))
    return csv_files


def aggregate_resources(csv_files):
    """Load and aggregate CPU/memory metrics by framework/OS."""
    metrics = defaultdict(lambda: {"cpu_avg": [], "cpu_peak": [], "mem_avg": [], "mem_peak": []})

    for condition, csv_path in csv_files:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                framework = row.get("framework", "").capitalize()
                os_name = row.get("os", "").capitalize()
                if not framework or not os_name:
                    continue

                key = f"{os_name} / {framework}"
                try:
                    metrics[key]["cpu_avg"].append(float(row.get("cpu_avg", 0)))
                    metrics[key]["cpu_peak"].append(float(row.get("cpu_peak", 0)))
                    metrics[key]["mem_avg"].append(float(row.get("mem_avg_mb", 0)))
                    metrics[key]["mem_peak"].append(float(row.get("mem_peak_mb", 0)))
                except ValueError:
                    continue

    # Compute means for each key
    aggregated = {}
    for key, values in metrics.items():
        aggregated[key] = {
            "cpu_avg": np.mean(values["cpu_avg"]) if values["cpu_avg"] else 0,
            "cpu_peak": np.mean(values["cpu_peak"]) if values["cpu_peak"] else 0,
            "mem_avg": np.mean(values["mem_avg"]) if values["mem_avg"] else 0,
            "mem_peak": np.mean(values["mem_peak"]) if values["mem_peak"] else 0,
        }

    return aggregated


def plot_resources(aggregated, output_dir):
    """Create grouped bar charts for CPU and Memory metrics."""
    if not aggregated:
        raise RuntimeError("No aggregated data available.")

    conditions = sorted(aggregated.keys())
    cpu_avg_vals = [aggregated[c]["cpu_avg"] for c in conditions]
    cpu_peak_vals = [aggregated[c]["cpu_peak"] for c in conditions]
    mem_avg_vals = [aggregated[c]["mem_avg"] for c in conditions]
    mem_peak_vals = [aggregated[c]["mem_peak"] for c in conditions]

    x = np.arange(len(conditions))
    width = 0.35

    # CPU plot
    fig_cpu, ax_cpu = plt.subplots(figsize=(7.0, 4.5))
    bars_avg = ax_cpu.bar(x - width / 2, cpu_avg_vals, width, label="Average CPU (%)",
                         color="lightblue", edgecolor="black", linewidth=0.5)
    bars_peak = ax_cpu.bar(x + width / 2, cpu_peak_vals, width, label="Peak CPU (%)",
                          color="darkblue", edgecolor="black", linewidth=0.5, alpha=0.7)

    ax_cpu.set_xlabel("Condition (OS / Framework)", fontsize=10)
    ax_cpu.set_ylabel("CPU Usage (%)", fontsize=10)
    ax_cpu.set_title("CPU Usage by Condition", fontsize=11, fontweight="bold")
    ax_cpu.set_xticks(x)
    ax_cpu.set_xticklabels(conditions, rotation=30, ha="right", fontsize=9)
    ax_cpu.legend(fontsize=9)
    ax_cpu.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.5)
    ax_cpu.set_axisbelow(True)
    # Annotate bars with numeric values (rounded to 1 decimal)
    for rect in list(bars_avg) + list(bars_peak):
        h = rect.get_height()
        ax_cpu.text(rect.get_x() + rect.get_width() / 2, h + max(0.01 * max(cpu_peak_vals + [1]), 0.5),
                    f"{h:.1f}", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    cpu_base_path = os.path.join(output_dir, "plot_resource_summary_cpu")
    cpu_pdf = f"{cpu_base_path}.pdf"
    cpu_png = f"{cpu_base_path}.png"
    fig_cpu.savefig(cpu_pdf, dpi=300, bbox_inches="tight", format="pdf")
    fig_cpu.savefig(cpu_png, dpi=300, bbox_inches="tight")
    plt.close(fig_cpu)

    # Memory plot
    fig_mem, ax_mem = plt.subplots(figsize=(7.0, 4.5))
    bars_mem_avg = ax_mem.bar(x - width / 2, mem_avg_vals, width, label="Average Memory (MB)",
                             color="lightcoral", edgecolor="black", linewidth=0.5)
    bars_mem_peak = ax_mem.bar(x + width / 2, mem_peak_vals, width, label="Peak Memory (MB)",
                              color="darkred", edgecolor="black", linewidth=0.5, alpha=0.7)

    ax_mem.set_xlabel("Condition (OS / Framework)", fontsize=10)
    ax_mem.set_ylabel("Memory Usage (MB)", fontsize=10)
    ax_mem.set_title("Memory Usage by Condition", fontsize=11, fontweight="bold")
    ax_mem.set_xticks(x)
    ax_mem.set_xticklabels(conditions, rotation=30, ha="right", fontsize=9)
    ax_mem.legend(fontsize=9)
    ax_mem.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.5)
    ax_mem.set_axisbelow(True)
    # Annotate memory bars
    for rect in list(bars_mem_avg) + list(bars_mem_peak):
        h = rect.get_height()
        ax_mem.text(rect.get_x() + rect.get_width() / 2, h + max(0.01 * max(mem_peak_vals + [1]), 1.0),
                    f"{h:.1f}", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    mem_base_path = os.path.join(output_dir, "plot_resource_summary_memory")
    mem_pdf = f"{mem_base_path}.pdf"
    mem_png = f"{mem_base_path}.png"
    fig_mem.savefig(mem_pdf, dpi=300, bbox_inches="tight", format="pdf")
    fig_mem.savefig(mem_png, dpi=300, bbox_inches="tight")
    plt.close(fig_mem)

    print(f"Saved resource charts to:")
    print(f"  CPU PDF: {cpu_pdf}")
    print(f"  CPU PNG: {cpu_png}")
    print(f"  Memory PDF: {mem_pdf}")
    print(f"  Memory PNG: {mem_png}")


def parse_args():
    root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "output", "10runs")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots")

    parser = argparse.ArgumentParser(
        description="Generate grouped bar charts for CPU and Memory usage by framework/OS from resource_summary.csv files."
    )
    parser.add_argument(
        "--input-dir",
        default=root_dir,
        help="Directory containing 10runs condition subfolders with resource_summary.csv files.",
    )
    parser.add_argument(
        "--output-dir",
        default=output_dir,
        help="Directory where output charts will be saved.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    csv_files = find_resource_csvs(args.input_dir)
    if not csv_files:
        raise FileNotFoundError(f"No resource_summary.csv files found in: {args.input_dir}")

    aggregated = aggregate_resources(csv_files)
    plot_resources(aggregated, args.output_dir)


if __name__ == "__main__":
    main()
