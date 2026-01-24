import json
import os
import matplotlib

from config import FRAMEWORK, OS, BROWSER, HEADLESS

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)

import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright.png") 

def get_total_execution_time(framework, os_name, browser, headless):
    report_path = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_get_all_tests_{framework}_{os_name}_{browser}_{headless}.json")
    if not os.path.exists(report_path):
        print(f"Warning: Report file not found for {framework}-{os_name}-{browser}-{headless}: {report_path}")
        return 0.0
    with open(report_path, "r") as f:
        data = json.load(f)
    total_time = sum(test["total"] for test in data)
    return total_time

# Define the configurations to compare
frameworks = ["selenium", "playwright"]
browsers = ["chrome", "firefox", "edge"]
os_name = "linux"
headless = "true"

selenium_totals = []
playwright_totals = []

for browser in browsers:
    selenium_totals.append(get_total_execution_time("selenium", os_name, browser, headless))
    playwright_totals.append(get_total_execution_time("playwright", os_name, browser, headless))

# Plotting
x = range(len(browsers))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

rects1 = ax.bar([i - width/2 for i in x], selenium_totals, width, label='Selenium', color='skyblue')
rects2 = ax.bar([i + width/2 for i in x], playwright_totals, width, label='Playwright', color='lightcoral')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Total Execution Time (seconds)')
ax.set_title(f'Total Execution Time: Selenium vs Playwright\n{FRAMEWORK} | {OS} | {BROWSER} | Headless: {HEADLESS}')
ax.set_xticks(x)
ax.set_xticklabels(browsers)
ax.legend()

fig.tight_layout()
plt.savefig(OUTPUT, bbox_inches="tight")