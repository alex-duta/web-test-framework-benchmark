# Genrate a bar plot comparing Selenium and Playwright resource summary for the same OS and browser configurations

# data\output\selenium_vs_playwright\01 win,selenium,chrome,headless-report\resource_summary.csv
# data\output\selenium_vs_playwright\01 win,playwright,chrome,headless-report\resource_summary.csv
# data\output\selenium_vs_playwright\02 linux,selenium,chrome,headless-report\resource_summary.csv
# data\output\selenium_vs_playwright\02 linux,playwright,chrome,headless-report\resource_summary.csv

import os
import matplotlib

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
OS = "Windows"
BROWSER = "Chrome"
HEADLESS = "true"
OUTPUT_CPU = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright_resource_summary_cpu_{OS}_{BROWSER}_{HEADLESS}.png")
OUTPUT_MEM = os.path.join(current_dir, "..", "plots", f"plot_selenium_vs_playwright_resource_summary_mem_{OS}_{BROWSER}_{HEADLESS}.png")

selenium_resource_summary_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,selenium,chrome,headless-report/resource_summary.csv")
playwright_resource_summary_path = os.path.join(current_dir, "..", "data/output/selenium_vs_playwright/01 win,playwright,chrome,headless-report/resource_summary.csv")
def parse_resource_summary(file_path):
    if not os.path.exists(file_path):
        print(f"Warning: Resource summary file not found: {file_path}")
        return None
    with open(file_path, "r") as f:
        lines = f.readlines()
    headers = lines[0].strip().split(",")
    data = []
    for line in lines[1:]:
        values = line.strip().split(",")
        entry = dict(zip(headers, values))
        data.append(entry)
    return data

selenium_data = parse_resource_summary(selenium_resource_summary_path)
playwright_data = parse_resource_summary(playwright_resource_summary_path)

# plot bar charts comparing cpu and mem metrics for both frameworks
cpu_labels = ['CPU Avg', 'CPU Peak']
mem_labels = ['Mem Avg (MB)', 'Mem Peak (MB)']
selenium_cpu_values = []
selenium_mem_values = []
playwright_cpu_values = []
playwright_mem_values = []

for entry in selenium_data:
    selenium_cpu_values.append(float(entry["cpu_avg"]))
    selenium_cpu_values.append(float(entry["cpu_peak"]))
    selenium_mem_values.append(float(entry["mem_avg_mb"]))
    selenium_mem_values.append(float(entry["mem_peak_mb"]))
    break  # only one entry expected

for entry in playwright_data:
    playwright_cpu_values.append(float(entry["cpu_avg"]))
    playwright_cpu_values.append(float(entry["cpu_peak"]))
    playwright_mem_values.append(float(entry["mem_avg_mb"]))
    playwright_mem_values.append(float(entry["mem_peak_mb"]))
    break  # only one entry expected

# CPU Plot
x_cpu = range(len(cpu_labels))
width = 0.35
fig_cpu, ax_cpu = plt.subplots(figsize=(10, 6))
rects1_cpu = ax_cpu.bar([p - width/2 for p in x_cpu], selenium_cpu_values, width, label='Selenium', color='skyblue')
rects2_cpu = ax_cpu.bar([p + width/2 for p in x_cpu], playwright_cpu_values, width, label='Playwright', color='lightcoral')
ax_cpu.set_ylabel('CPU Usage (%)')
ax_cpu.set_title(f'CPU Usage: Selenium vs Playwright\n {OS} | {BROWSER} | Headless: {HEADLESS}')
ax_cpu.set_xticks(x_cpu)
ax_cpu.set_xticklabels(cpu_labels)
ax_cpu.legend()

# Add value labels on CPU bars
for rect in rects1_cpu:
    height = rect.get_height()
    ax_cpu.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
for rect in rects2_cpu:
    height = rect.get_height()
    ax_cpu.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)

fig_cpu.tight_layout()
plt.savefig(OUTPUT_CPU, bbox_inches="tight")
plt.close(fig_cpu)

# Memory Plot
x_mem = range(len(mem_labels))
fig_mem, ax_mem = plt.subplots(figsize=(10, 6))
rects1_mem = ax_mem.bar([p - width/2 for p in x_mem], selenium_mem_values, width, label='Selenium', color='skyblue')
rects2_mem = ax_mem.bar([p + width/2 for p in x_mem], playwright_mem_values, width, label='Playwright', color='lightcoral')
ax_mem.set_ylabel('Memory Usage (MB)')
ax_mem.set_title(f'Memory Usage: Selenium vs Playwright\n {OS} | {BROWSER} | Headless: {HEADLESS}')
ax_mem.set_xticks(x_mem)
ax_mem.set_xticklabels(mem_labels)
ax_mem.legend()

# Add value labels on Memory bars
for rect in rects1_mem:
    height = rect.get_height()
    ax_mem.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
for rect in rects2_mem:
    height = rect.get_height()
    ax_mem.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)

fig_mem.tight_layout()
plt.savefig(OUTPUT_MEM, bbox_inches="tight")
plt.close(fig_mem)