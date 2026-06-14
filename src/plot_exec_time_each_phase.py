import json
import os
import matplotlib

from config import FRAMEWORK, OS, BROWSER, HEADLESS

matplotlib.use("Agg")   # non-GUI backend (CI / Windows-safe)

import matplotlib.pyplot as plt

# py .\src\plot_exec_time_each_phase.py
current_dir = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_get_all_tests_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.json")

OUTPUT = os.path.join(current_dir, "..", "plots", f"plot_exec_time_each_phase_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.png") 

results = json.load(open(REPORT, "r"))  # your JSON list

labels = [r["id"] for r in results]

#from test name (e.g. "tests/test_user_dialogs.py::test_prompt_dialog_enter_text_and_accept[Prompt dialog was shown, text entered and accepted]") extract just the tst function name (e.g. "test_prompt_dialog_enter_text_and_accept")
labels = [l.split("::")[-1].split("[")[0] for l in labels]

setup = [r["setup"] for r in results]
call = [r["call"] for r in results]
teardown = [r["teardown"] for r in results]

x = range(len(labels))

plt.figure(figsize=(12, 6))  # make figure bigger

# show the total time on the plot
for i, total_val in enumerate([setup[i] + call[i] + teardown[i] for i in range(len(results))]):
    plt.text(i, total_val, str(round(total_val, 2)), ha='center', va='bottom')

# show the setp, call and teardown times on te plot
for i in range(len(results)):
    plt.text(i, setup[i] / 2, str(round(setup[i], 2)), ha='center', va='center', color='white')
    plt.text(i, setup[i] + call[i] / 2, str(round(call[i], 2)), ha='center', va='center', color='white')
    plt.text(i, setup[i] + call[i] + teardown[i] / 2, str(round(teardown[i], 2)), ha='center', va='center', color='white')
    
plt.bar(x, setup, label="setup")
plt.bar(x, call, bottom=setup, label="call")
plt.bar(x, teardown, bottom=[setup[i] + call[i] for i in range(len(results))], label="teardown")

plt.xticks(x, labels, rotation=45, ha="right")  # rotate labels
plt.ylabel("Execution time (seconds)")
plt.title(f"Total Test Execution Time Breakdown\n{FRAMEWORK} | {OS} | {BROWSER} | Headless: {HEADLESS}")
plt.legend()

#add setup, call, teardown total execution time outside the plot
total_setup_time = sum(setup)
total_call_time = sum(call)
total_teardown_time = sum(teardown)
total_times = [total_setup_time + total_call_time + total_teardown_time]

plt.figtext(0.99, 0.15, f"Total Setup Time: {round(total_setup_time, 2)} seconds", horizontalalignment='right', verticalalignment='bottom', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
plt.figtext(0.99, 0.10, f"Total Call Time: {round(total_call_time, 2)} seconds", horizontalalignment='right', verticalalignment='bottom', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
plt.figtext(0.99, 0.05, f"Total Teardown Time: {round(total_teardown_time, 2)} seconds", horizontalalignment='right', verticalalignment='bottom', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))


plt.tight_layout(pad=2.0)  # add padding so labels don't get cut
plt.savefig(OUTPUT, bbox_inches="tight")  # save as file
    