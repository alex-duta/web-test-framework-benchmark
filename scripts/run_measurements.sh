#!/usr/bin/env bash
# Runs a measurement series with the Selenium and Playwright test frameworks and archives the
# results of every session. See the README of test-metrics-analyzer for the full instructions.
#
# What the script does, for each browser given on the command line:
#   1. one warm-up session per framework (archived under warmup/, excluded from the analysis);
#   2. SESSIONS measured sessions per framework, each running the whole test suite REPS times.
#      The framework that runs first alternates from session to session, so that neither
#      framework always runs at the same point in time.
# After every session, the reports are moved from <repo>/reports/ into an archive folder, and a
# one-line summary (passed/failed, mean suite time) is printed.
#
# Usage:  [VARIABLE=value ...] scripts/run_measurements.sh [browser ...]
#         browsers: chrome, edge, firefox (default: all three)
#
# Settings (environment variables):
#   RUN_FOLDER       name of the measurement series; results go to reports/runs/RUN_FOLDER/ (required)
#   RUN_SET          subfolder inside RUN_FOLDER, e.g. 10runs, 50runs           (default 50runs)
#   MODE             local = tests run on this machine (Windows only)
#                    docker = tests run in the framework containers            (default local)
#   FRAMEWORKS_ROOT  folder that contains both framework repositories
#                    (default: the folder that contains test-metrics-analyzer)
#   APP_URL          address of the application under test          (default http://localhost:3000/)
#   SESSIONS         measured sessions per browser and framework               (default 5)
#   REPS             suite repetitions per session                              (default 10)
#   WARMUP_REPS      repetitions of the warm-up session, 0 to skip it           (default 1)
#   FRAMEWORKS       frameworks to run                             (default "selenium playwright")
#   MONITOR          true = record CPU and memory, false = measure time only    (default false)
#
# Results, in each framework repository:
#   reports/runs/RUN_FOLDER/RUN_SET/<nn> <os>,<framework>,<browser>,headless-report/
#       session_01/ ... session_NN/   one folder per session (files directly here if SESSIONS=1)
#       warmup/                       the warm-up session
#   <nn> is 01 for Chrome, 02 for Firefox, 03 for Edge; <os> is win (local) or linux (docker).

# Treat unset variables as errors.
set -u
# Git Bash on Windows: do not rewrite arguments that look like paths (e.g. in docker commands).
export MSYS_NO_PATHCONV=1

# ---------------------------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------------------------

# Print the current folder as a Windows path (C:/...) in Git Bash, which python.exe and
# powershell.exe understand; on other systems print the normal path.
native_pwd() { pwd -W 2>/dev/null || pwd; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && native_pwd)"
DEFAULT_ROOT="$(cd "$(dirname "$0")/../.." && native_pwd)"   # the folder that contains test-metrics-analyzer
ROOT="${FRAMEWORKS_ROOT:-$DEFAULT_ROOT}"
RUN_FOLDER=${RUN_FOLDER:?set RUN_FOLDER to the name of the measurement series, e.g. RUN_FOLDER=series_01}
RUN_SET=${RUN_SET:-50runs}
MODE=${MODE:-local}
APP_URL=${APP_URL:-http://localhost:3000/}
SESSIONS=${SESSIONS:-5}
REPS=${REPS:-10}
WARMUP_REPS=${WARMUP_REPS:-1}
FRAMEWORKS=${FRAMEWORKS:-selenium playwright}
MONITOR=${MONITOR:-false}

# Browsers from the command line, or all three.
BROWSERS=("$@")
[ ${#BROWSERS[@]} -eq 0 ] && BROWSERS=(chrome edge firefox)

# The OS label becomes part of the result folder name and is used by the analysis.
# Local runs are supported on Windows only: the analysis treats "linux" as the Docker environment.
case "$MODE" in
    local)
        case "$(uname -s)" in
            MINGW*|MSYS*|CYGWIN*) OS_LABEL=win ;;
            *) echo "!! MODE=local is supported on Windows (Git Bash) only; use MODE=docker"; exit 1 ;;
        esac ;;
    docker) OS_LABEL=linux ;;
    *) echo "!! MODE must be local or docker"; exit 1 ;;
esac

# Number of each browser in the result folder name, and the Playwright options that select it.
# (Selenium selects the browser through the BROWSER environment variable instead.)
declare -A NUM=([chrome]=01 [firefox]=02 [edge]=03)
declare -A PW_ARGS=([chrome]="--browser-channel chrome" [edge]="--browser-channel msedge" [firefox]="--browser firefox")

# Windows only: keep the machine from going to sleep while the script runs. No power setting
# is changed; the helper stops by itself when this script ends, and after 12 hours at most.
WINPID=$(cat /proc/$$/winpid 2>/dev/null)   # Windows process id of this script (Git Bash only)
if [ -n "$WINPID" ]; then
    powershell -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/keep_awake.ps1" -ParentPid "$WINPID" >/dev/null &
    echo "keep-awake helper started"
fi

# ---------------------------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------------------------

# Move the reports of the session that just finished from <repo>/reports/ to the archive folder.
# Stops the script if the session produced no report (the run failed) or if the archive folder
# already holds a report, so that no result is ever overwritten.
archive() {  # $1 = framework repository, $2 = archive folder
    local repo="$1" dest="$2"
    if [ ! -f "$repo/reports/report.json" ]; then
        echo "!! no report.json produced (run failed or Docker dropped), stopping"; exit 1
    fi
    # a warmup/ subfolder may already exist in dest; only an existing report counts as a clash
    if [ -f "$dest/report.json" ]; then
        echo "!! $dest already has a report, refusing to overwrite; results left in $repo/reports"; exit 1
    fi
    mkdir -p "$dest"
    mv "$repo/reports/report.html" "$repo/reports/report.json" "$dest/"
    mv "$repo"/reports/*.png "$dest/" 2>/dev/null   # end-of-test screenshots
    for f in resource_summary.csv resource_samples.csv; do   # only present when MONITOR=true
        [ -f "$repo/reports/$f" ] && mv "$repo/reports/$f" "$dest/"
    done
}

# Print a one-line summary of a session from its report.json: test outcomes, number of data
# resets, browser versions, and the mean and SD of the suite time over the complete repetitions.
summarize() {  # $1 = report.json
    "$PYTHON" - "$1" <<'EOF'
import json, re, sys, collections, statistics as st
r = json.load(open(sys.argv[1], encoding="utf-8"))
tot, bad = collections.defaultdict(float), set()
for t in r["tests"]:
    m = re.search(r"(\d+)-\d+\]$", t["nodeid"])  # repetition number; absent with --count=1
    k = int(m.group(1)) if m else 1
    tot[k] += sum(float(t.get(p, {}).get("duration") or 0) for p in ("setup", "call", "teardown"))
    if t["outcome"] != "passed":
        bad.add(k)
good = [tot[k] for k in sorted(tot) if k not in bad]
line = f"{r['summary']}  resets={r.get('data_reset', {}).get('resets')}  {r.get('browsers')}"
if len(good) > 1:
    line += f"  complete reps={len(good)} mean={st.mean(good):.1f}s sd={st.stdev(good):.2f}"
print("   " + line)
for t in r["tests"]:
    if t["outcome"] != "passed":
        print(f"   NOT PASSED ({t['outcome']}): {t['nodeid'].split('::')[1]}")
EOF
}

# Python of a framework repository's virtual environment (Windows or Linux/macOS layout).
venv_python() {  # $1 = framework repository
    if [ -x "$1/.venv/Scripts/python.exe" ]; then echo "$1/.venv/Scripts/python.exe"; else echo "$1/.venv/bin/python"; fi
}

# Run one session: the whole test suite, repeated `count` times, for one framework and browser.
# pytest options: -m smoke selects the 17 tests, --count repeats the suite (pytest-repeat, with
# the session repeat scope set in the frameworks' pyproject.toml), --reset-app-data empties the
# application's user list before every repetition, -p no:cacheprovider leaves no cache behind.
run_session() {  # $1 = framework, $2 = browser, $3 = session number or "warmup"
    local fw="$1" browser="$2" s="$3"
    local count=$REPS
    local repo="$ROOT/$fw-python-framework"
    local dest="$repo/reports/runs/$RUN_FOLDER/$RUN_SET/${NUM[$browser]} $OS_LABEL,$fw,$browser,headless-report"
    if [ "$s" = warmup ]; then
        dest="$dest/warmup"; count=$WARMUP_REPS
    elif [ "$SESSIONS" -gt 1 ]; then
        dest="$dest/session_$(printf %02d "$s")"
    fi
    local extra=""
    [ "$fw" = playwright ] && extra="${PW_ARGS[$browser]}"
    echo "=== $(date '+%d.%m %H:%M:%S') $browser session $s/$SESSIONS: $fw x$count ($MODE) ==="
    if [ "$MODE" = docker ]; then
        # run pytest inside the already running test container of the framework
        ( cd "$repo" && docker compose exec -T -e BROWSER="$browser" -e MONITOR_RESOURCES="$MONITOR" "${fw}_tests" \
            pytest -m smoke -q -p no:cacheprovider --reset-app-data --count=$count $extra 2>&1 \
            | grep -E "passed|failed|error|WARNING" | tail -2 )
    else
        # run pytest on this machine with the repository's virtual environment
        ( cd "$repo" && BROWSER="$browser" MONITOR_RESOURCES="$MONITOR" \
            "$(venv_python "$repo")" -m pytest -m smoke -q -p no:cacheprovider --reset-app-data --count=$count $extra 2>&1 \
            | grep -E "passed|failed|error|WARNING" | tail -2 )
    fi
    archive "$repo" "$dest"
    summarize "$dest/report.json"
}

# ---------------------------------------------------------------------------------------------
# Checks before starting: stop early rather than produce an incomplete series
# ---------------------------------------------------------------------------------------------

for fw in $FRAMEWORKS; do
    # the framework repository exists
    [ -d "$ROOT/$fw-python-framework" ] || { echo "!! $ROOT/$fw-python-framework not found (set FRAMEWORKS_ROOT), stopping"; exit 1; }
    # reports/ holds nothing but the archive, so no old file ends up in a session's results
    if ls "$ROOT/$fw-python-framework/reports" 2>/dev/null | grep -qv '^runs$'; then
        echo "!! $fw reports/ has leftover files, stopping:"; ls "$ROOT/$fw-python-framework/reports"; exit 1
    fi
    # in Docker mode, the framework's test container is running
    if [ "$MODE" = docker ] && [ "$(docker inspect -f '{{.State.Running}}' "${fw}_tests" 2>/dev/null)" != true ]; then
        echo "!! container ${fw}_tests is not running, stopping"; exit 1
    fi
done
# the application under test answers
code=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL")
[ "$code" = 200 ] || { echo "!! application not reachable at $APP_URL (HTTP $code), stopping"; exit 1; }
# a Python interpreter for the session summaries (any Python 3 will do; "python" is tried first
# because on Windows "python3" may be the Microsoft Store placeholder)
PYTHON=$(command -v python || command -v python3) || { echo "!! python not found, stopping"; exit 1; }

echo "measurements start $(date '+%d.%m.%Y %H:%M:%S'), mode: $MODE, browsers: ${BROWSERS[*]}, $SESSIONS x $REPS repetitions, warm-up $WARMUP_REPS, frameworks: $FRAMEWORKS, monitoring: $MONITOR"

# ---------------------------------------------------------------------------------------------
# Measurement series
# ---------------------------------------------------------------------------------------------

b_index=0
for browser in "${BROWSERS[@]}"; do
    # warm-up: starts browsers and drivers once, so the first measured session is not slower
    if [ "$WARMUP_REPS" -gt 0 ]; then
        for fw in $FRAMEWORKS; do
            run_session "$fw" "$browser" warmup
        done
    fi
    for s in $(seq 1 "$SESSIONS"); do
        # Alternate which framework goes first: odd sessions start with Selenium, even ones with
        # Playwright. With a single session per browser, alternate from browser to browser instead.
        first=$s
        [ "$SESSIONS" -eq 1 ] && first=$((b_index + 1))
        if [ $((first % 2)) -eq 1 ]; then order="selenium playwright"; else order="playwright selenium"; fi
        for fw in $order; do
            [[ " $FRAMEWORKS " == *" $fw "* ]] || continue   # skip frameworks not selected
            run_session "$fw" "$browser" "$s"
        done
    done
    b_index=$((b_index + 1))
done
echo "measurements end $(date '+%d.%m.%Y %H:%M:%S')"
