"""
Generate the aggregated metrics for each phaseI(setup, call, teardown) from the report.json file.
"""
import json
import os

from config import FRAMEWORK, OS, BROWSER, HEADLESS

current_dir = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(current_dir, "..", "data/input", "report.json")
OUTPUT = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_aggregate_each_phase_all_tests_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.json") 

with open(REPORT, "r") as f:
    data = json.load(f)

tests = data["tests"]

report_body = []
# take each phase execution time ad calculate the total (e.g. total setup time)
total_setup_time = sum(test["setup"]["duration"] for test in tests)
total_call_time = sum(test["call"]["duration"] for test in tests)
total_teardown_time = sum(test["teardown"]["duration"] for test in tests)

report_body.append({
    "id": "Total Execution Times",
    "status": "N/A",
    "setup": round(total_setup_time, 3),
    "call": round(total_call_time, 3),
    "teardown": round(total_teardown_time, 3),
    "total": round(total_setup_time + total_call_time + total_teardown_time, 3)
})

with open(OUTPUT, "w") as f:
    json.dump(report_body, f, indent=2)