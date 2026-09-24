# AI Eval Harness

A small Python tool that scores AI model responses against **explicit, testable criteria** and produces a structured report of what failed and why.

It covers the core loop of AI output evaluation: define test prompts with expected criteria, collect responses, score them, tag failures, and track consistency across repeated runs.

> **About the sample data:** the responses in `data/sample_responses.csv` are **hand-written examples** for two fictional models (`demo-model-a`, `demo-model-b`). They exist to demonstrate the harness and are **not** real benchmark results. Use the `live` command or your own CSV to score real models.

## What it checks

| Criterion | Column in `test_cases.csv` | Example |
|---|---|---|
| Accuracy | `must_include` | `Canberra`, or alternatives `17:05/5:05` |
| Forbidden content | `must_not_include` | `green`, `aircrack` |
| Format | `format` | `json`, `bullets:3`, `numbered:3`, `one_sentence`, `number_only` |
| Length | `max_words` | `25` |
| Consistency | repeated `run` rows | do runs of one prompt agree on pass/fail? |

A response **passes** only if every applicable criterion is met. It also gets a 0-100 score (accuracy 40, forbidden content 20, format 20, length 20, re-weighted to the criteria that apply) so results can be ranked.

## Quick start

```bash
git clone https://github.com/hashesgenb65-dev/ai-eval-harness.git
cd ai-eval-harness
pip install -r requirements.txt

python -m evalharness run          # scores data/sample_responses.csv
pytest                              # 26 unit tests
```

Sample output:

```
model                 passed   pass rate   avg score
----------------------------------------------------
demo-model-a        10/16          62.5%        79.2
demo-model-b        12/17          70.6%        83.8
```

It also writes `reports/results.csv` and `reports/report.md` (pass rate by category, failure-tag counts, consistency flags, and a table of every failed response with the reason). A generated example is committed in [`reports/report.md`](reports/report.md).

## Score your own model

Provide a CSV with columns `model,id,run,response` where `id` matches a case in `data/test_cases.csv`:

```bash
python -m evalharness run --responses my_responses.csv --out reports
python -m evalharness run --fail-under 0.8     # exit code 1 if a model is below 80%: usable as a CI gate
```

Optional live mode calls the Anthropic Messages API to collect responses:

```bash
export ANTHROPIC_API_KEY=...
python -m evalharness live --runs 3 --out data/live_responses.csv
python -m evalharness run --responses data/live_responses.csv
```

## Layout

```
evalharness/
  core.py      loading, rule checks, scoring, consistency
  report.py    console summary, CSV and Markdown report
  live.py      optional response generation via the API
  cli.py       command line interface
data/          14 test cases across factual, arithmetic, reasoning, format,
               instruction-following, safety and hallucination-trap categories
tests/         26 unit tests for the checks and scoring
docs/failure-taxonomy.md   failure categories and how each is detected
```

## Design notes and limitations

- Checks are **deterministic rules**, so results are reproducible and easy to explain. They cannot judge tone, depth of reasoning or nuance; those need human review or a validated LLM-as-judge step. See [`docs/failure-taxonomy.md`](docs/failure-taxonomy.md).
- Term matching is whole-word and case-insensitive, so `Au` does not match "because".
- The safety case only checks that a refusal phrase appears and that specific harmful terms do not. It is a smoke test, not a safety evaluation.
- 14 cases is a demonstration set, not a statistically meaningful benchmark.

## Skills demonstrated

Python, AI model evaluation, prompt testing, test-case design, rubric-based scoring, failure analysis, consistency testing, CSV data handling, pytest, CI with GitHub Actions.
