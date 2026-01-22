"""
Generate the metrics for all tests from the raw report.json file.
"""
import json
import os

from config import FRAMEWORK, OS, BROWSER, HEADLESS

# py .\src\parser_exec_time_get_all_tests.py
current_dir = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(current_dir, "..", "data/input", "report.json")

OUTPUT = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_get_all_tests_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.json") 

with open(REPORT, "r") as f:
    data = json.load(f)

tests = data["tests"]

report_body = []
for test in tests:
    report_body.append({
        "id": test["nodeid"],
        "status": test["outcome"],
        "setup": round(test["setup"]["duration"], 3),
        "call": round(test["call"]["duration"], 3),
        "teardown": round(test["teardown"]["duration"], 3),
        "total": round(
            test["setup"]["duration"] +
            test["call"]["duration"] +
            test["teardown"]["duration"], 3
        )
    })

with open(OUTPUT, "w") as f:
    json.dump(report_body, f, indent=2)
