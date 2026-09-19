# Test Metrics Analyzer

Runs repeated measurement series with the [Selenium](https://github.com/alexduta-tech/selenium-python-framework) and [Playwright](https://github.com/alexduta-tech/playwright-python-framework) test frameworks against the [Automation Playground](https://github.com/alexduta-tech/automation-lab) application, and computes execution-time and resource statistics from the results.

It works in two steps:

1. **Measure:** `scripts/run_measurements.sh` runs both test suites many times and archives every report in the framework repositories.
2. **Analyse:** the Python scripts in `src/` read those reports and compute the statistics.

## Setup

1. **Put the repositories side by side** in one folder:
   ```
   workspace/
   ├── automation-lab/
   ├── selenium-python-framework/
   ├── playwright-python-framework/
   └── test-metrics-analyzer/
   ```
   If the framework repositories are somewhere else, set `FRAMEWORKS_ROOT` to the folder that contains them, for both the measurements and the analysis.
2. **Install the analyzer:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

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
- **Sleep:** on Windows, the script keeps the machine from going to sleep while it runs, using `scripts/keep_awake.ps1`. No power setting is changed.

### Before you start

1. **Install both frameworks.**
   - For `MODE=local`: set up each framework's `.venv` as described in its README.
   - For `MODE=docker`: start each framework's container (`run_selenium_docker.bat` / `run_playwright_docker.bat`, or `docker compose up -d`).
2. **Start the application** in the matching mode: its local installation for `MODE=local`, its Docker installation for `MODE=docker`. See the automation-lab README.
3. **Empty the `reports/` folders:** in both framework repositories, `reports/` must contain nothing except `runs/`.
4. **Keep the machine idle:** close browsers and other programs, and pause updates.

### Settings

Settings are environment variables, written in front of the command.

| Variable | Default | Meaning |
|---|---|---|
| `RUN_FOLDER` | (required) | Name of the measurement series; results go to `reports/runs/<RUN_FOLDER>/` |
| `RUN_SET` | `50runs` | Subfolder inside `RUN_FOLDER`; the analysis expects `10runs`, `50runs` and `50runs_resources` |
| `MODE` | `local` | `local` or `docker` |
| `FRAMEWORKS_ROOT` | the folder that contains `test-metrics-analyzer` | Folder that contains both framework repositories |
| `APP_URL` | `http://localhost:3000/` | Address of the application, checked before starting |
| `SESSIONS` | `5` | Measured sessions per browser and framework |
| `REPS` | `10` | Suite repetitions per session |
| `WARMUP_REPS` | `1` | Repetitions of the warm-up session; `0` skips the warm-up |
| `FRAMEWORKS` | `selenium playwright` | Frameworks to run, e.g. `FRAMEWORKS=selenium` |
| `MONITOR` | `false` | `true` also records CPU and memory. Use it only for resource series: recording uses CPU itself |

The browsers are given as arguments: `chrome`, `edge`, `firefox` (all three if none is given).

### Examples

Run these from the `test-metrics-analyzer` folder in Git Bash. They collect the three run sets that the analysis expects, first on Windows and then in Docker.

```bash
# 1. Cross-browser: 10 repetitions per browser, in one session
RUN_FOLDER=series_01 RUN_SET=10runs MODE=local SESSIONS=1 scripts/run_measurements.sh chrome edge firefox
RUN_FOLDER=series_01 RUN_SET=10runs MODE=docker SESSIONS=1 scripts/run_measurements.sh chrome edge firefox

# 2. Repeated execution: Chrome, 5 sessions of 10 repetitions
RUN_FOLDER=series_01 RUN_SET=50runs MODE=local scripts/run_measurements.sh chrome
RUN_FOLDER=series_01 RUN_SET=50runs MODE=docker scripts/run_measurements.sh chrome

# 3. Resource utilization: as 2, with CPU and memory recording
RUN_FOLDER=series_01 RUN_SET=50runs_resources MODE=local MONITOR=true scripts/run_measurements.sh chrome
RUN_FOLDER=series_01 RUN_SET=50runs_resources MODE=docker MONITOR=true scripts/run_measurements.sh chrome
```

Switch the application to its Docker installation before the `MODE=docker` runs.

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

Then run:

```powershell
py src\parse_reports.py        # reports -> one row per suite repetition
py src\compute_statistics.py   # statistics for every comparison
```

| Script | Output (in `data\output\`) |
|---|---|
| `parse_reports.py` | `<run folder>_repetitions.csv`: one row per suite repetition, with setup, call and teardown durations, outcome and browser versions. `<run folder>_resources.csv`: CPU and memory per repetition (resource series only) |
| `compute_statistics.py` | `<run folder>_statistics.csv`: mean, SD, median, 95% CI, min, max, ratio, A12 and p-value for every comparison (columns explained in [STATISTICS.md](STATISTICS.md)); also prints a summary |

What is analysed:

- The three run sets `10runs`, `50runs` and `50runs_resources` of the series.
- Warm-up sessions and folders outside the run sets (for example `superseded/`) are ignored.
- Repetitions that contain a failed test are excluded from the statistics and listed by `parse_reports.py`.

Other settings, such as the run sets and the resource sampling interval, are in `src/config.py`.

## Tables and figures for publication

`src/paper/` builds LaTeX tables and figures from the same CSV files. It is not needed for the analysis.

```powershell
py src\paper\latex_tables.py   # LaTeX tables in data\output\
py src\paper\make_plots.py     # figures in plots\<run folder>\ (PDF and PNG)
```

## How to cite

If you use this repository in your work, please cite it as described in [CITATION.cff](CITATION.cff) (on GitHub: "Cite this repository").

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
