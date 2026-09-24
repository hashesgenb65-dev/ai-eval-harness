from __future__ import annotations

import argparse
import sys

from . import live
from .core import check_consistency, evaluate, load_cases, load_responses
from .report import console_summary, summarize, write_reports


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="evalharness", description="Score AI responses against explicit criteria.")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="score saved responses")
    run.add_argument("--cases", default="data/test_cases.csv")
    run.add_argument("--responses", default="data/sample_responses.csv")
    run.add_argument("--out", default="reports")
    run.add_argument("--fail-under", type=float, default=None, metavar="RATE",
                     help="exit with status 1 if any model's pass rate (0-1) is below RATE")

    gen = sub.add_parser("live", help="generate responses from a model (needs ANTHROPIC_API_KEY)")
    gen.add_argument("--cases", default="data/test_cases.csv")
    gen.add_argument("--out", default="data/live_responses.csv")
    gen.add_argument("--model", default=live.DEFAULT_MODEL)
    gen.add_argument("--runs", type=int, default=1)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "live":
        n = live.generate(load_cases(args.cases), args.out, args.model, args.runs)
        print(f"Wrote {n} responses to {args.out}")
        return 0

    cases = load_cases(args.cases)
    results = evaluate(cases, load_responses(args.responses))
    consistency = check_consistency(results)
    csv_path, md_path = write_reports(cases, results, consistency, args.out)
    summary = summarize(results)
    print(console_summary(summary))
    print(f"\nWrote {csv_path} and {md_path}")

    if args.fail_under is not None and any(s["pass_rate"] < args.fail_under for s in summary.values()):
        print(f"FAIL: a model is below the required pass rate of {args.fail_under:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
