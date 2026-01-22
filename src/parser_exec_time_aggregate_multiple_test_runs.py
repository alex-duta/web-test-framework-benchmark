"""
Generate the aggregated metrics and combine all runs for each test from the report.json file.
"""
import json
import os

from config import FRAMEWORK, OS, BROWSER, HEADLESS

current_dir = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(current_dir, "..", "data/input", "report.json")
OUTPUT = os.path.join(current_dir, "..", "data/output", f"parser_exec_time_aggregate_multiple_test_runs_{FRAMEWORK}_{OS}_{BROWSER}_{HEADLESS}.json") 

with open(REPORT, "r") as f:
    data = json.load(f)

tests = data["tests"]

# aggregate test based on number of executions, e.g. tests/test_create_users.py::test_create_10_users[1-2], tests/test_create_users.py::test_create_10_users[2-2]
aggregated_tests = {}
for test in tests:
    nodeid_parts = test["nodeid"].split("::")
    test_id_with_params = nodeid_parts[-1]
    
    # Remove the parameter part, e.g., "[1-2]" or "[param]"
    base_test_id = test_id_with_params.split("[")[0]
    
    # Reconstruct a common ID for aggregation
    common_id = "::".join(nodeid_parts[:-1] + [base_test_id])

    if common_id not in aggregated_tests:
        aggregated_tests[common_id] = {
            "nodeid": common_id,
            "setup": [],
            "call": [],
            "teardown": [],
            "outcome": []
        }
    aggregated_tests[common_id]["setup"].append(test["setup"]["duration"])
    aggregated_tests[common_id]["call"].append(test["call"]["duration"])
    aggregated_tests[common_id]["teardown"].append(test["teardown"]["duration"])
    aggregated_tests[common_id]["outcome"].append(test["outcome"])

# Calculate averages for aggregated tests
processed_tests = []
for common_id, data in aggregated_tests.items():
    avg_setup = sum(data["setup"]) / len(data["setup"])
    avg_call = sum(data["call"]) / len(data["call"])
    avg_teardown = sum(data["teardown"]) / len(data["teardown"])
    
    # Determine overall status: if any failed, mark as failed, otherwise passed
    overall_status = "passed"
    if "failed" in data["outcome"]:
        overall_status = "failed"
    elif "skipped" in data["outcome"]:
        overall_status = "skipped"

    processed_tests.append({
        "nodeid": common_id,
        "outcome": overall_status,
        "setup": {"duration": avg_setup},
        "call": {"duration": avg_call},
        "teardown": {"duration": avg_teardown}
    })

tests = processed_tests

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
