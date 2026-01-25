# generate a grouped bar plot comparing Selenium and Playwright performance for the same OS and browser configurations

import json
import os
import matplotlib

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

current_dir = os.path.dirname(os.path.abspath(__file__))
OS = "Linux"
BROWSER = "Chrome"
HEADLESS = "true"
OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright_exec_time_{OS}_{BROWSER}_{HEADLESS}.png")

# read the report.json files for both frameworks based on file names and paths provided
# selenium_report_path_win = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,selenium,chrome,headless-report/report.json")
# playwright_report_path_win = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,playwright,chrome,headless-report/report.json")

selenium_report_path_linux = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/02 linux,selenium,chrome,headless-report/report.json")
playwright_report_path_linux = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/02 linux,playwright,chrome,headless-report/report.json")

# use "duration"
def get_total_execution_time(report_path):
    if not os.path.exists(report_path):
        print(f"Warning: Report file not found: {report_path}")
        return 0.0
    with open(report_path, "r") as f:
        data = json.load(f)
    # Extract total duration from the report JSON
    total_time = float(data.get("duration", 0.0))
    return total_time

selenium_total = get_total_execution_time(selenium_report_path_linux)
playwright_total = get_total_execution_time(playwright_report_path_linux)

# Plotting 
labels = ['Selenium', 'Playwright']
totals = [selenium_total, playwright_total]

fig, ax = plt.subplots(figsize=(10, 6))

# Create bars for Selenium and Playwright side by side
x_pos = [0, 1]
rects = ax.bar(x_pos, totals, width=0.6, color=['skyblue', 'lightcoral'])
ax.set_ylabel('Total Execution Time (mm:ss)')
ax.set_title(f'Total Execution Time: Selenium vs Playwright\n Selenium | Playwright | {OS} | {BROWSER} | Headless: {HEADLESS}')
ax.set_xticks(x_pos)
ax.set_xticklabels(labels)

# Add mm:ss labels on top of each bar
for i, (rect, total) in enumerate(zip(rects, totals)):
    minutes = int(total // 60)
    seconds = int(total % 60)
    label = f"{minutes}:{seconds:02d}"
    ax.text(rect.get_x() + rect.get_width()/2, rect.get_height(), label,
            ha='center', va='bottom', fontweight='bold', fontsize=11)

# Format y-axis to show mm:ss using FuncFormatter
def format_mmss(value, tick_number):
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes}:{seconds:02d}"

ax.yaxis.set_major_formatter(FuncFormatter(format_mmss))

fig.tight_layout()
plt.savefig(OUTPUT, bbox_inches="tight")
