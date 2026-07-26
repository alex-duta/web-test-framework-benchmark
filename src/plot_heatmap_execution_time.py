import argparse
import json
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


def find_condition_reports(root_dir):
    """Find all condition report.json files."""
    report_paths = []
    for entry in sorted(os.listdir(root_dir)):
        dir_path = os.path.join(root_dir, entry)
        report_file = os.path.join(dir_path, "report.json")
        if os.path.isdir(dir_path) and os.path.isfile(report_file):
            report_paths.append((entry, report_file))
    return report_paths


def parse_condition_label(label):
    """Parse condition label into OS, Framework, Browser.
    Example: '01 win,selenium,chrome,headless-report' -> ('Windows', 'Selenium', 'Chrome')
    """
    parts = label.replace("-report", "").split(",")
    if len(parts) >= 3:
        os_part = parts[0].strip().split()[-1].capitalize()  # Extract 'win' or 'linux'
        framework = parts[1].strip().capitalize()
        browser = parts[2].strip().capitalize()
        return os_part, framework, browser
    return None, None, None


def load_durations(report_path):
    """Load and return average test duration."""
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

    return np.mean(durations) if durations else 0.0


def build_matrix(report_items):
    """Build heatmap matrix: rows=OS/Framework, cols=Browser."""
    # Collect unique values
    os_frameworks = set()
    browsers = set()
    data_dict = defaultdict(dict)

    for condition, report_path in report_items:
        os_name, framework, browser = parse_condition_label(condition)
        if not all([os_name, framework, browser]):
            continue

        os_fw = f"{os_name}\n{framework}"
        os_frameworks.add(os_fw)
        browsers.add(browser)

        avg_duration = load_durations(report_path)
        data_dict[os_fw][browser] = avg_duration

    # Sort and create matrix
    os_fw_sorted = sorted(os_frameworks)
    browsers_sorted = sorted(browsers)

    matrix = np.zeros((len(os_fw_sorted), len(browsers_sorted)))
    for i, os_fw in enumerate(os_fw_sorted):
        for j, browser in enumerate(browsers_sorted):
            matrix[i, j] = data_dict[os_fw].get(browser, 0.0)

    return matrix, os_fw_sorted, browsers_sorted


def plot_heatmap(matrix, row_labels, col_labels, output_dir):
    """Create and save heatmap."""
    fig, ax = plt.subplots(figsize=(7, 5))

    # Create heatmap with diverging colormap
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto")

    # Set ticks and labels
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, fontsize=10)
    ax.set_yticklabels(row_labels, fontsize=10)

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Execution Time (seconds)", rotation=270, labelpad=20, fontsize=10)

    # Add text annotations
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            value = matrix[i, j]
            if value > 0:
                text = ax.text(
                    j, i, f"{value:.1f}s",
                    ha="center", va="center",
                    color="black" if value < matrix.max() / 2 else "white",
                    fontsize=9, fontweight="bold"
                )

    ax.set_xlabel("Browser", fontsize=10)
    ax.set_ylabel("OS / Framework", fontsize=10)
    ax.set_title("Execution Time Heatmap Across Conditions", fontsize=11, fontweight="bold")

    plt.tight_layout()

    # Save as PDF and PNG
    os.makedirs(output_dir, exist_ok=True)
    base_path = os.path.join(output_dir, "plot_heatmap_execution_time")
    output_pdf = f"{base_path}.pdf"
    output_png = f"{base_path}.png"

    plt.savefig(output_pdf, dpi=300, bbox_inches="tight", format="pdf")
    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved heatmap to:")
    print(f"  PDF: {output_pdf}")
    print(f"  PNG: {output_png}")


def parse_args():
    root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "output", "10runs")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots")

    parser = argparse.ArgumentParser(
        description="Generate a heatmap of execution times across OS/Framework/Browser conditions."
    )
    parser.add_argument(
        "--input-dir",
        default=root_dir,
        help="Directory containing 10runs condition subfolders with report.json files.",
    )
    parser.add_argument(
        "--output-dir",
        default=output_dir,
        help="Directory where output charts will be saved.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report_items = find_condition_reports(args.input_dir)
    if not report_items:
        raise FileNotFoundError(f"No condition report.json files found in: {args.input_dir}")

    matrix, row_labels, col_labels = build_matrix(report_items)
    if matrix.size == 0:
        raise RuntimeError("No data available for heatmap.")

    plot_heatmap(matrix, row_labels, col_labels, args.output_dir)


if __name__ == "__main__":
    main()
