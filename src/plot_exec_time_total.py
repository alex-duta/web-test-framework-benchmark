import json
import os
import matplotlib

from config import FRAMEWORK, OS, BROWSER, HEADLESS

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)

import matplotlib.pyplot as plt

# run: python -m .\src\plots\plot_status_and_exec_time.py
current_dir = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_get_all_tests_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.json")
OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_exec_time_total_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.png") 

results = json.load(open(REPORT, "r"))  # your JSON list

# plot execution time and status for each test
labels = [r["id"] for r in results]
#from test name (e.g. "tests/test_user_dialogs.py::test_prompt_dialog_enter_text_and_accept[Prompt dialog was shown, text entered and accepted]") extract just the tst function name (e.g. "test_prompt_dialog_enter_text_and_accept")
labels = [l.split("::")[-1].split("[")[0] for l in labels]

total_times = [r["total"] for r in results]
statuses = [r["status"] for r in results]

# Map statuses to colors
status_colors = {
    "passed": "green",
    "failed": "red",
    "skipped": "orange",
    "xfailed": "purple",
    "xpassed": "cyan"
}
colors = [status_colors.get(s, "gray") for s in statuses]

x = range(len(labels))

plt.figure(figsize=(12, 6))  # make figure bigger

bars = plt.bar(x, total_times, color=colors)

# Add total time values on top of the bars
for i, total_val in enumerate(total_times):
    plt.text(i, total_val, str(round(total_val, 2)), ha='center', va='bottom')

plt.xticks(x, labels, rotation=45, ha="right")  # rotate labels
plt.ylabel("Execution time (seconds)")
plt.title(f"Total Test Execution Time for Each Run\n{FRAMEWORK} | {OS} | {BROWSER} | Headless: {HEADLESS}")

#add total execution time 
plt.figtext(0.99, 0.01, f"Total Execution Time: {round(sum(total_times), 2)} seconds", horizontalalignment='right', verticalalignment='bottom', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))

# Create a legend manually
handles = [plt.Rectangle((0,0),1,1, color=status_colors[s]) for s in status_colors]
plt.legend(handles, status_colors.keys(), title="Status")

plt.tight_layout(pad=2.0)  # add padding so labels don't get cut
plt.savefig(OUTPUT, bbox_inches="tight")

    