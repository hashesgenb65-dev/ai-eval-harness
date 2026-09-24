"""Loading test cases and responses, and scoring each response against a rubric.

A response PASSES only if every applicable criterion is met. A numeric score
(0-100) is also produced so responses can be ranked and trends tracked.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Optional

# Failure tags used in reports (see docs/failure-taxonomy.md)
MISSING_FACT = "MISSING_FACT"
FORBIDDEN_CONTENT = "FORBIDDEN_CONTENT"
FORMAT_VIOLATION = "FORMAT_VIOLATION"
TOO_LONG = "TOO_LONG"
EMPTY = "EMPTY"
INCONSISTENT = "INCONSISTENT"

WEIGHTS = {"accuracy": 40, "forbidden": 20, "format": 20, "length": 20}


@dataclass
class Case:
    id: str
    category: str
    prompt: str
    must_include: list = field(default_factory=list)      # list of alternative-lists
    must_not_include: list = field(default_factory=list)  # list of strings
    max_words: Optional[int] = None
    fmt: str = ""


@dataclass
class Check:
    name: str
    passed: bool
    fraction: float
    tag: Optional[str]
    detail: str


@dataclass
class Result:
    model: str
    case_id: str
    run: int
    category: str
    response: str
    score: float
    passed: bool
    checks: list
    tags: list

    @property
    def failure_details(self) -> str:
        return "; ".join(c.detail for c in self.checks if not c.passed)


# ------------------------------------------------------------------ loading
def _split(value: str, sep: str = "|") -> list:
    return [p.strip() for p in (value or "").split(sep) if p.strip()]


def load_cases(path) -> list:
    cases = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cases.append(
                Case(
                    id=row["id"].strip(),
                    category=row.get("category", "").strip() or "general",
                    prompt=row["prompt"].strip(),
                    must_include=[_split(t, "/") for t in _split(row.get("must_include", ""))],
                    must_not_include=_split(row.get("must_not_include", "")),
                    max_words=int(row["max_words"]) if (row.get("max_words") or "").strip() else None,
                    fmt=(row.get("format") or "").strip().lower(),
                )
            )
    return cases


def load_responses(path) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "model": (row.get("model") or "model").strip(),
                    "id": row["id"].strip(),
                    "run": int(row.get("run") or 1),
                    "response": row.get("response") or "",
                }
            )
    return rows


# ------------------------------------------------------------------ checks
def term_present(term: str, text: str) -> bool:
    """Case-insensitive, whole-word/phrase match (so 'Au' does not match 'because')."""
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE) is not None


def word_count(text: str) -> int:
    return len(text.split())


def check_format(fmt: str, text: str):
    """Return (ok, reason). Supported: json, bullets[:N], numbered[:N], one_sentence, number_only."""
    fmt = (fmt or "").strip().lower()
    if fmt in ("", "none"):
        return True, ""
    name, _, count = fmt.partition(":")
    stripped = text.strip()

    if name == "json":
        if stripped.startswith("```"):
            return False, "JSON wrapped in a code fence although 'JSON only' was requested"
        try:
            obj = json.loads(stripped)
        except ValueError as exc:
            return False, f"invalid JSON ({exc.msg})"
        return (True, "") if isinstance(obj, dict) else (False, "JSON is not an object")

    if name in ("bullets", "numbered"):
        pattern = r"^\s*[-*\u2022]\s+" if name == "bullets" else r"^\s*\d+[.)]\s+"
        items = [ln for ln in text.splitlines() if re.match(pattern, ln)]
        if not items:
            return False, f"no {name} list found"
        if count and len(items) != int(count):
            return False, f"expected {count} {name} items, found {len(items)}"
        return True, ""

    if name == "one_sentence":
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", stripped) if s]
        return (True, "") if len(sentences) == 1 else (False, f"expected 1 sentence, found {len(sentences)}")

    if name == "number_only":
        ok = re.fullmatch(r"\s*-?\d+(\.\d+)?\.?\s*", text) is not None
        return (True, "") if ok else (False, "response is not just a number")

    raise ValueError(f"unknown format rule: {fmt!r}")


def evaluate_response(case: Case, response: str, model: str = "model", run: int = 1) -> Result:
    checks = []

    if not response.strip():
        checks.append(Check("empty", False, 0.0, EMPTY, "empty response"))
        return Result(model, case.id, run, case.category, response, 0.0, False, checks, [EMPTY])

    if case.must_include:
        missing = [alts for alts in case.must_include if not any(term_present(a, response) for a in alts)]
        found = len(case.must_include) - len(missing)
        detail = "missing: " + ", ".join("/".join(m) for m in missing) if missing else ""
        checks.append(
            Check("accuracy", not missing, found / len(case.must_include), MISSING_FACT if missing else None, detail)
        )

    if case.must_not_include:
        hits = [t for t in case.must_not_include if term_present(t, response)]
        detail = "contains forbidden: " + ", ".join(hits) if hits else ""
        checks.append(Check("forbidden", not hits, 0.0 if hits else 1.0, FORBIDDEN_CONTENT if hits else None, detail))

    if case.fmt:
        ok, reason = check_format(case.fmt, response)
        checks.append(Check("format", ok, 1.0 if ok else 0.0, None if ok else FORMAT_VIOLATION, reason))

    if case.max_words is not None:
        n = word_count(response)
        ok = n <= case.max_words
        detail = "" if ok else f"{n} words, limit {case.max_words}"
        checks.append(Check("length", ok, 1.0 if ok else 0.0, None if ok else TOO_LONG, detail))

    total_weight = sum(WEIGHTS[c.name] for c in checks) or 1
    score = 100 * sum(WEIGHTS[c.name] * c.fraction for c in checks) / total_weight
    tags = [c.tag for c in checks if c.tag]
    return Result(model, case.id, run, case.category, response, round(score, 1), all(c.passed for c in checks), checks, tags)


def evaluate(cases: list, responses: list) -> list:
    by_id = {c.id: c for c in cases}
    results = []
    for row in responses:
        case = by_id.get(row["id"])
        if case is None:
            raise KeyError(f"response refers to unknown case id {row['id']!r}")
        results.append(evaluate_response(case, row["response"], row["model"], row["run"]))
    return results


# ------------------------------------------------------------- consistency
@dataclass
class Consistency:
    model: str
    case_id: str
    runs: int
    similarity: float
    outcomes_agree: bool


def check_consistency(results: list) -> list:
    """For every (model, case) with several runs: do the runs agree on pass/fail,
    and how similar are the answers (0-1)?"""
    groups = defaultdict(list)
    for r in results:
        groups[(r.model, r.case_id)].append(r)
    out = []
    for (model, case_id), rs in sorted(groups.items()):
        if len(rs) < 2:
            continue
        sims = [SequenceMatcher(None, a.response.lower(), b.response.lower()).ratio() for a, b in combinations(rs, 2)]
        out.append(Consistency(model, case_id, len(rs), round(sum(sims) / len(sims), 2), len({r.passed for r in rs}) == 1))
    return out
