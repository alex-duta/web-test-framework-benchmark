# Statistics output

`py comparative_evaluation_selenium_playwright\compute_statistics.py` writes `data\output\<run folder>_statistics.csv`, with one row per comparison. This file explains what is compared and what each column means.

## What is compared

| `data_set` | `comparison` | Groups |
|---|---|---|
| `10runs` | `framework` | Selenium vs Playwright, per OS and browser (10 repetitions each) |
| `50runs` | `framework` | Selenium vs Playwright, per OS, Chrome (50 repetitions each) |
| `50runs` | `environment (<framework>)` | Windows vs Linux for one framework, Chrome |
| `50runs_resources` | `framework` | Selenium vs Playwright, per OS, Chrome, resource metrics |

Group A is always the first group named (`group_a`, for example Selenium or Windows); group B is the second.

`metric` is what is measured per repetition:

| `metric` | Meaning |
|---|---|
| `total_s` | Suite execution time: setup + call + teardown of the 17 tests (s) |
| `call_s` | Time spent on test actions (s) |
| `setup_teardown_s` | Time spent in test setup and teardown, mainly starting and closing the browser (s) |
| `cpu_avg`, `cpu_peak` | Average and peak CPU utilization, summed over processes and cores (%) |
| `cpu_time_s` | Average CPU utilization × duration of the repetition (CPU seconds) |
| `mem_avg_mb`, `mem_peak_mb` | Average and peak resident memory, summed over processes (MB) |

Repetitions containing a failed test and warm-up sessions are excluded.

## Columns

The columns ending in `_a` describe group A, those ending in `_b` group B.

| Column | Meaning |
|---|---|
| `n` | Number of repetitions |
| `mean` | Average of the per-repetition values |
| `sd` | Standard deviation: how far individual repetitions typically lie from the mean |
| `median` | Middle value when the repetitions are sorted; unlike the mean, hardly affected by outliers |
| `ci_low`, `ci_high` | 95% confidence interval of the mean, `mean ± t(0.975, n−1) × sd / √n`: the range that very likely contains the true average. It narrows as repetitions are added; the SD does not. |
| `min`, `max` | Fastest and slowest repetition |
| `ratio_a_b` | `mean_a / mean_b`, e.g. 2.35 = group A took 2.35 times as long |
| `a12` | Vargha–Delaney effect size: the probability that a repetition of group A has a larger value than a repetition of group B. 0.5 = no difference, 1.0 = every A repetition larger than every B repetition, 0.0 = the opposite. Computed by comparing all pairs of repetitions. |
| `a12_magnitude` | Size of the effect: negligible (A12 within 0.44–0.56), small (up to 0.36/0.64), medium (up to 0.29/0.71), large (beyond) |
| `p_value` | Two-sided Mann–Whitney U test: the probability of a difference at least this large if both groups had the same distribution. Below 0.05 means the difference is unlikely to be chance. The test ranks all values together, so it assumes no particular distribution and is robust to outliers. |

`a12` and the Mann–Whitney test are based on the same ranking: `a12 = U / (n_a × n_b)`.

## Example

With made-up values: a row for `10runs`, `total_s`, `win`, `chrome` with `mean_a` 60.0, `sd_a` 1.0, `mean_b` 30.0, `ratio_a_b` 2.0, `a12` 1.0 and `p_value` 0.000183 means:
- Selenium (group A) needed on average 60.0 ± 1.0 s per suite repetition and Playwright (group B) 30.0 s, twice as long;
- every Selenium repetition was slower than every Playwright repetition;
- a difference this large is very unlikely to be chance.
