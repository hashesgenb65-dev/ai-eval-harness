"""Turn evaluation results into a console summary, a CSV and a Markdown report."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


def summarize(results: list) -> dict:
    models = defaultdict(list)
    for r in results:
        models[r.model].append(r)
    summary = {}
    for model, rs in models.items():
        cats = defaultdict(list)
        for r in rs:
            cats[r.category].append(r)
        summary[model] = {
            "total": len(rs),
            "passed": sum(r.passed for r in rs),
            "pass_rate": sum(r.passed for r in rs) / len(rs),
            "avg_score": sum(r.score for r in rs) / len(rs),
            "categories": {c: (sum(x.passed for x in v), len(v)) for c, v in sorted(cats.items())},
            "tags": Counter(t for r in rs for t in r.tags),
        }
    return summary


def console_summary(summary: dict) -> str:
    lines = [f"{'model':<18}{'passed':>10}{'pass rate':>12}{'avg score':>12}", "-" * 52]
    for model, s in sorted(summary.items()):
        lines.append(f"{model:<18}{s['passed']:>4}/{s['total']:<5}{s['pass_rate']*100:>11.1f}%{s['avg_score']:>12.1f}")
    return "\n".join(lines)


def write_results_csv(results: list, path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "id", "run", "category", "passed", "score", "failure_tags", "details"])
        for r in results:
            w.writerow([r.model, r.case_id, r.run, r.category, r.passed, r.score, " ".join(r.tags), r.failure_details])


def _esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(cases: list, results: list, consistency: list) -> str:
    summary = summarize(results)
    prompts = {c.id: c.prompt for c in cases}
    out = ["# Evaluation report", ""]

    out += ["## Summary", "", "| Model | Passed | Pass rate | Avg score |", "|---|---|---|---|"]
    for model, s in sorted(summary.items()):
        out.append(f"| {model} | {s['passed']}/{s['total']} | {s['pass_rate']*100:.1f}% | {s['avg_score']:.1f} |")

    out += ["", "## Pass rate by category", ""]
    categories = sorted({c for s in summary.values() for c in s["categories"]})
    out.append("| Category | " + " | ".join(sorted(summary)) + " |")
    out.append("|---|" + "---|" * len(summary))
    for cat in categories:
        cells = []
        for model in sorted(summary):
            p, t = summary[model]["categories"].get(cat, (0, 0))
            cells.append(f"{p}/{t}" if t else "-")
        out.append(f"| {cat} | " + " | ".join(cells) + " |")

    out += ["", "## Failure tags", "", "| Tag | " + " | ".join(sorted(summary)) + " |", "|---|" + "---|" * len(summary)]
    all_tags = sorted({t for s in summary.values() for t in s["tags"]})
    for tag in all_tags:
        out.append(f"| {tag} | " + " | ".join(str(summary[m]["tags"].get(tag, 0)) for m in sorted(summary)) + " |")

    inconsistent = [c for c in consistency if not c.outcomes_agree]
    out += ["", "## Consistency across repeated runs", ""]
    if not consistency:
        out.append("No case has more than one run, so consistency was not measured.")
    elif not inconsistent:
        out.append("All repeated runs agreed on pass/fail.")
    else:
        out += ["Cases where repeated runs disagreed on pass/fail:", "", "| Model | Case | Runs | Mean text similarity |", "|---|---|---|---|"]
        out += [f"| {c.model} | {c.case_id} | {c.runs} | {c.similarity} |" for c in inconsistent]

    failures = [r for r in results if not r.passed]
    out += ["", f"## Failed responses ({len(failures)})", ""]
    if failures:
        out += ["| Model | Case | Run | Category | Why it failed | Prompt |", "|---|---|---|---|---|---|"]
        for r in sorted(failures, key=lambda x: (x.model, x.case_id, x.run)):
            out.append(
                f"| {r.model} | {r.case_id} | {r.run} | {r.category} | {_esc(r.failure_details)} | {_esc(prompts.get(r.case_id, ''))} |"
            )
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def write_reports(cases, results, consistency, out_dir) -> tuple:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path, md_path = out_dir / "results.csv", out_dir / "report.md"
    write_results_csv(results, csv_path)
    md_path.write_text(to_markdown(cases, results, consistency), encoding="utf-8")
    return csv_path, md_path
