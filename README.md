# Web Test Framework Benchmark

Scripts for measuring and comparing web test automation frameworks. Each comparison has its own folder, with a README that explains how to run the measurements and the analysis.

| Folder | Content |
|---|---|
| [comparative_evaluation_selenium_playwright/](comparative_evaluation_selenium_playwright/) | Repeated measurement series with the [Selenium](https://github.com/alex-duta/selenium-python-framework) and [Playwright](https://github.com/alex-duta/playwright-python-framework) test frameworks against the [Automation Playground](https://github.com/alex-duta/automation-lab) application, on Windows and in Docker, and the execution-time and resource statistics computed from them |

## Setup

All folders use the same Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Data

The measurement data are not stored in the repository: `data/` is ignored by git, and the scripts write their results to `data/output/`. When the data of a measurement series are published, they are attached as a zip archive to a release of this repository.

## How to cite

If you use this repository in your work, please cite it as described in [CITATION.cff](CITATION.cff) (on GitHub: "Cite this repository").

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
