# generate a grouped bar plot comparing Selenium and Playwright pass rates for the same OS and browser configurations

import json
import os
import matplotlib

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

current_dir = os.path.dirname(os.path.abspath(__file__))
OS = "Windows"
BROWSER = "Chrome"
HEADLESS = "true"

if OS == "Windows":
    OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright_pass_rate_{OS}_{BROWSER}_{HEADLESS}.png")
    selenium_report_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,selenium,chrome,headless-report/report.json")
    playwright_report_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,playwright,chrome,headless-report/report.json")
else:
    OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright_pass_rate_{OS}_{BROWSER}_{HEADLESS}.png")
    selenium_report_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/02 linux,selenium,chrome,headless-report/report.json")
    playwright_report_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/02 linux,playwright,chrome,headless-report/report.json")

def get_test_count(report_path):
    if not os.path.exists(report_path):
        print(f"Warning: Report file not found: {report_path}")
        return 0, 0
    with open(report_path, "r") as f:
        data = json.load(f)
    summary = data.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    return passed, total

selenium_passed, selenium_test_count = get_test_count(selenium_report_path)
playwright_passed, playwright_test_count = get_test_count(playwright_report_path)

selenium_pass_rate = (selenium_passed / selenium_test_count * 100) if selenium_test_count > 0 else 0
playwright_pass_rate = (playwright_passed / playwright_test_count * 100) if playwright_test_count > 0 else 0

# Plotting 
labels = ['Selenium', 'Playwright']
test_counts = [selenium_test_count, playwright_test_count]
pass_rates = [selenium_pass_rate, playwright_pass_rate]

fig, ax = plt.subplots(figsize=(10, 6))

# Create bars for Selenium and Playwright side by side
x_pos = [0, 1]
rects = ax.bar(x_pos, test_counts, width=0.6, color=['skyblue', 'lightcoral'])
ax.set_ylabel('Number of Tests')
ax.set_title(f'Test Count: Selenium vs Playwright\n {OS} | {BROWSER} | Headless: {HEADLESS}')
ax.set_xticks(x_pos)
ax.set_xticklabels(labels)

# Add pass rate labels on top of each bar
for i, (rect, pass_rate) in enumerate(zip(rects, pass_rates)):
    ax.text(rect.get_x() + rect.get_width()/2, rect.get_height(), f"{pass_rate:.1f}%",
            ha='center', va='bottom', fontweight='bold', fontsize=11)

fig.tight_layout()
plt.savefig(OUTPUT, bbox_inches="tight")