# Comparative Evaluation of Selenium and Playwright

Runs repeated measurement series with the [Selenium](https://github.com/alex-duta/selenium-python-framework) and [Playwright](https://github.com/alex-duta/playwright-python-framework) test frameworks against the [Automation Playground](https://github.com/alex-duta/automation-lab) application, and computes execution-time and resource statistics from the results.

The scripts in this folder work in two steps:

1. **Measure:** `run_measurements.sh` runs both test suites many times and archives every report in the framework repositories.
2. **Analyse:** the Python scripts next to it read those reports and compute the statistics.

## Setup

1. **Put the repositories side by side** in one folder:
   ```
   workspace/
   ├── automation-lab/
   ├── selenium-python-framework/
   ├── playwright-python-framework/
   └── web-test-framework-benchmark/
   ```
   If the framework repositories are somewhere else, set `FRAMEWORKS_ROOT` to the folder that contains them, for both the measurements and the analysis.
2. **Install the Python environment** as described in the [main README](../README.md#setup).

## 1. Measure

### What the script does

For each browser you give it:

1. **Warm-up:** each framework runs the test suite once. The result is kept under `warmup/` but not analysed. The first start of browsers and drivers is slower, and this keeps it out of the measurements.
2. **Measured sessions:** each framework runs `SESSIONS` sessions. In each session the whole suite (17 tests) runs `REPS` times in a row, with the application's user list emptied before every repetition. The framework that goes first alternates between sessions.
3. **Archiving:** after each session, the reports are moved from the framework's `reports/` folder into an archive folder, and a one-line summary is printed (tests passed/failed, mean suite time).

The script stops, rather than continuing with incomplete data, if:
- a framework repository or its test container is missing;
- `reports/` contains leftover files;
- the application does not answer;
- a session produces no report;
- a result folder already contains a report. Results are never overwritten.

### Where it runs

| Host | `MODE=local` (tests run on the host) | `MODE=docker` (tests run in containers) |
|---|---|---|
| Windows | Yes, in Git Bash | Yes, in Git Bash |
| Linux, macOS | No | Yes (needs Bash 4 or newer) |

- **Git Bash** comes with [Git for Windows](https://git-scm.com/download/win). Run the script from a Git Bash window, not from PowerShell or cmd.
- **Local mode is Windows only.** The analysis labels local results `win` and Docker results `linux`.
- **Sleep:** on Windows, the script keeps the machine from going to sleep while it runs, using `keep_awake.ps1` from the same folder. No power setting is changed.

### Before you start

1. **Install both frameworks.**
   - For `MODE=local`: set up each framework's `.venv` as described in its README.
   - For `MODE=docker`: start each framework's container (`run_selenium_docker.bat` / `run_playwright_docker.bat`, or `docker compose up -d`).
2. **Start the application set up for the matching mode:** for local execution with `MODE=local`, for Docker execution with `MODE=docker` (in automation-lab, `run_frontend_backend.bat` asks which one; see its README). With the wrong setup, the tests cannot reach the application's backend.
3. **Empty the `reports/` folders:** in both framework repositories, `reports/` must contain nothing except `runs/`.
4. **Keep the machine idle:** close browsers and other programs, and pause updates.

### Settings

Settings are environment variables, written in front of the command.

| Variable | Default | Meaning |
|---|---|---|
| `RUN_FOLDER` | (required) | Name of the measurement series; results go to `reports/runs/<RUN_FOLDER>/` |
| `RUN_SET` | `50runs` | Subfolder inside `RUN_FOLDER`; the analysis expects `10runs`, `50runs` and `50runs_resources` |
| `MODE` | `local` | `local` or `docker` |
| `FRAMEWORKS_ROOT` | the folder that contains `web-test-framework-benchmark` | Folder that contains both framework repositories |
| `APP_URL` | `http://localhost:3000/` | Address of the application, checked before starting |
| `SESSIONS` | `5` | Measured sessions per browser and framework |
| `REPS` | `10` | Suite repetitions per session |
| `WARMUP_REPS` | `1` | Repetitions of the warm-up session; `0` skips the warm-up |
| `FRAMEWORKS` | `selenium playwright` | Frameworks to run, e.g. `FRAMEWORKS=selenium` |
| `MONITOR` | `false` | `true` also records CPU and memory. Use it only for resource series: recording uses CPU itself |

The browsers are given as arguments: `chrome`, `edge`, `firefox` (all three if none is given).

### Examples

Run these from the `web-test-framework-benchmark` folder in Git Bash. All examples run both frameworks, alternating them, except example 2, which runs only Playwright (`FRAMEWORKS=playwright`). Examples 1 and 2 are quick checks that everything works. Examples 3 to 5 collect the three run sets that the analysis expects.

Each example has a `MODE=local` and a `MODE=docker` version, and each mode needs automation-lab set up for it. Run all the local commands first, then switch automation-lab once and run the Docker commands.

**A. Tests on Windows (`MODE=local`).** First start automation-lab set up for local execution: in automation-lab, run `run_frontend_backend.bat` and answer **Y**.

```bash
# automation-lab must be set up for LOCAL execution (run_frontend_backend.bat, answer Y)

# 1. Quick check, both frameworks: 1 repetition in Chrome, no warm-up (its own RUN_FOLDER and RUN_SET, not analysed)
RUN_FOLDER=trial RUN_SET=1run MODE=local SESSIONS=1 REPS=1 WARMUP_REPS=0 comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 2. Quick check, Playwright only: as 1, for one framework
RUN_FOLDER=trial_playwright RUN_SET=1run MODE=local SESSIONS=1 REPS=1 WARMUP_REPS=0 FRAMEWORKS=playwright comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 3. Cross-browser: 10 repetitions per browser, in one session
RUN_FOLDER=series_01 RUN_SET=10runs MODE=local SESSIONS=1 REPS=10 comparative_evaluation_selenium_playwright/run_measurements.sh chrome edge firefox

# 4. Repeated execution: 50 repetitions in Chrome, in 5 sessions of 10
RUN_FOLDER=series_01 RUN_SET=50runs MODE=local SESSIONS=5 REPS=10 comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 5. Resource utilization: as 4, with CPU and memory recording
RUN_FOLDER=series_01 RUN_SET=50runs_resources MODE=local SESSIONS=5 REPS=10 MONITOR=true comparative_evaluation_selenium_playwright/run_measurements.sh chrome
```

**B. Tests in Docker (`MODE=docker`).** First restart automation-lab set up for Docker execution: in automation-lab, run `run_frontend_backend.bat` and answer **N**. On Linux and macOS, only this mode is available.

```bash
# automation-lab must be set up for DOCKER execution (run_frontend_backend.bat, answer N)

# 1. Quick check, both frameworks
RUN_FOLDER=trial RUN_SET=1run MODE=docker SESSIONS=1 REPS=1 WARMUP_REPS=0 comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 2. Quick check, Playwright only
RUN_FOLDER=trial_playwright RUN_SET=1run MODE=docker SESSIONS=1 REPS=1 WARMUP_REPS=0 FRAMEWORKS=playwright comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 3. Cross-browser
RUN_FOLDER=series_01 RUN_SET=10runs MODE=docker SESSIONS=1 REPS=10 comparative_evaluation_selenium_playwright/run_measurements.sh chrome edge firefox

# 4. Repeated execution
RUN_FOLDER=series_01 RUN_SET=50runs MODE=docker SESSIONS=5 REPS=10 comparative_evaluation_selenium_playwright/run_measurements.sh chrome

# 5. Resource utilization
RUN_FOLDER=series_01 RUN_SET=50runs_resources MODE=docker SESSIONS=5 REPS=10 MONITOR=true comparative_evaluation_selenium_playwright/run_measurements.sh chrome
```

Results are never overwritten, so to repeat a quick check, delete its folder under `reports/runs/` (`trial/` in both framework repositories, `trial_playwright/` in the Playwright repository) or use another `RUN_FOLDER`.

### Results

In each framework repository:

```
reports/runs/<RUN_FOLDER>/<RUN_SET>/<nn> <os>,<framework>,<browser>,headless-report/
    session_01/ ... session_05/      one folder per session (files directly here if SESSIONS=1)
    warmup/                          the warm-up session, not analysed
```

- `<nn>` is `01` for Chrome, `02` for Firefox, `03` for Edge; `<os>` is `win` (local) or `linux` (Docker).
- Each session folder holds `report.json`, `report.html`, the screenshots and, with `MONITOR=true`, `resource_samples.csv` and `resource_summary.csv`.

**If the script stops in the middle:** the results of the failed session stay in `reports/`. Move them away, move the folder of the unfinished configuration into `reports/runs/<RUN_FOLDER>/superseded/` (the analysis ignores it), then start that browser again.

## 2. Analyse

Tell the scripts which measurement series to read, using the same values as for the measurements:

```powershell
$env:RUN_FOLDER = "series_01"                    # required
$env:FRAMEWORKS_ROOT = "C:\path\to\workspace"    # only if the framework repositories are not next to this one
```

Then run, from the `web-test-framework-benchmark` folder:

```powershell
py comparative_evaluation_selenium_playwright\parse_reports.py        # reports -> one row per suite repetition
py comparative_evaluation_selenium_playwright\compute_statistics.py   # statistics for every comparison
```

| Script | Output (in `data\output\` of the repository) |
|---|---|
| `parse_reports.py` | `<run folder>_repetitions.csv`: one row per suite repetition, with setup, call and teardown durations, outcome and browser versions. `<run folder>_resources.csv`: CPU and memory per repetition (resource series only) |
| `compute_statistics.py` | `<run folder>_statistics.csv`: mean, SD, median, 95% CI, min, max, ratio, A12 and p-value for every comparison (columns explained in [STATISTICS.md](STATISTICS.md)); also prints a summary |

What is analysed:

- The three run sets `10runs`, `50runs` and `50runs_resources` of the series.
- Warm-up sessions and folders outside the run sets (for example `superseded/`) are ignored.
- Repetitions that contain a failed test are excluded from the statistics and listed by `parse_reports.py`.

Other settings, such as the run sets and the resource sampling interval, are in [config.py](config.py).

## Troubleshooting

**`!! <folder>/<framework>-python-framework not found (set FRAMEWORKS_ROOT), stopping`**

The script looks for the framework repositories in the folder that contains `web-test-framework-benchmark`, and they are not there. Set `FRAMEWORKS_ROOT` to the folder that contains them, in front of the command, for example with example 1:

```bash
FRAMEWORKS_ROOT=C:/path/to/folder RUN_FOLDER=trial RUN_SET=1run MODE=local SESSIONS=1 REPS=1 WARMUP_REPS=0 comparative_evaluation_selenium_playwright/run_measurements.sh chrome
```

or once for the whole Git Bash window:

```bash
export FRAMEWORKS_ROOT=C:/path/to/folder
```

On Linux and macOS, use the normal path form, e.g. `/path/to/folder`. The analysis scripts need the same setting, in PowerShell: `$env:FRAMEWORKS_ROOT = "C:\path\to\folder"`.
