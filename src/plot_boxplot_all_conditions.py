import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    "figure.figsize": (6.5, 4.5),  # Single-column width for 2-column layout
    "axes.edgecolor": "black",
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.5,
    "figure.dpi": 100,
})

# run: python src/plot_boxplot_all_conditions.py --input-dir data/output/10runs --output plots/plot_boxplot_execution_time_all_conditions.png
def find_condition_reports(root_dir):
    report_paths = []
    # iterate through all subdirectories in the root_dir to find report.json files
    for entry in sorted(os.listdir(root_dir)):
        dir_path = os.path.join(root_dir, entry)
        report_file = os.path.join(dir_path, "report.json")
        if os.path.isdir(dir_path) and os.path.isfile(report_file):
            report_paths.append((entry, report_file))
    return report_paths


def load_durations(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    durations = []
    for test in data.get("tests", []):
        if test.get("outcome") != "passed":
            continue

        duration = test.get("duration")
        if duration is None:
            setup = test.get("setup", {}).get("duration", 0.0)
            call = test.get("call", {}).get("duration", 0.0)
            teardown = test.get("teardown", {}).get("duration", 0.0)
            duration = setup + call + teardown

        if duration is not None:
            durations.append(duration)

    return durations


def format_condition_label(raw_label):
    parts = [part.strip() for part in raw_label.split(",") if part.strip()]
    if len(parts) >= 3:
        os_name = parts[0].split()[1].capitalize() if " " in parts[0] else parts[0].capitalize()
        framework = parts[1].capitalize()
        browser = parts[2].capitalize()
        return f"{os_name} / {framework} / {browser}"
    return raw_label


def plot_boxplot(condition_data, output_path):
    labels = [format_condition_label(condition) for condition, _ in condition_data]
    values = [durations for _, durations in condition_data]

    fig, ax = plt.subplots()
    box = ax.boxplot(
        values,
        labels=labels,
        patch_artist=True,
        showfliers=True,
        medianprops={"color": "black", "linewidth": 1.0},
        boxprops={"facecolor": "lightgray", "edgecolor": "black", "linewidth": 0.5},
        whiskerprops={"color": "black", "linewidth": 0.5},
        capprops={"color": "black", "linewidth": 0.5},
        flierprops={"marker": "o", "markerfacecolor": "black", "markersize": 3, "alpha": 0.6},
    )

    ax.set_title("Execution Time Distribution Across Test Conditions", fontsize=11, fontweight="bold")
    ax.set_xlabel("Condition (OS / Framework / Browser)", fontsize=10)
    ax.set_ylabel("Total Test Execution Time (seconds)", fontsize=10)
    ax.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.5)
    ax.set_axisbelow(True)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Save as PDF (vector format, preferred for IEEE)
    output_pdf = output_path.replace(".png", ".pdf")
    plt.savefig(output_pdf, dpi=300, bbox_inches="tight", format="pdf")
    # Save as PNG (raster format, for quick viewing)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved boxplot to:")
    print(f"  PDF: {output_pdf}")
    print(f"  PNG: {output_path}")


def parse_args():
    root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "output", "10runs")
    default_output = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots", "plot_boxplot_execution_time_all_conditions.png")

    parser = argparse.ArgumentParser(
        description="Generate a boxplot of total execution time per condition from all 10runs report files."
    )
    parser.add_argument(
        "--input-dir",
        default=root_dir,
        help="Directory containing 10runs condition subfolders with report.json files.",
    )
    parser.add_argument(
        "--output",
        default=default_output,
        help="Output PNG file path for the generated boxplot.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report_items = find_condition_reports(args.input_dir)
    if not report_items:
        raise FileNotFoundError(f"No condition report.json files found in: {args.input_dir}")

    condition_data = []
    for condition, report_path in report_items:
        durations = load_durations(report_path)
        if not durations:
            print(f"Warning: no passed test durations found in {report_path}")
            continue
        condition_data.append((condition, durations))

    if not condition_data:
        raise RuntimeError("No duration data available for plotting.")

    plot_boxplot(condition_data, args.output)


if __name__ == "__main__":
    main()
