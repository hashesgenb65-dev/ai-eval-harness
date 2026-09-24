"""Optional: generate responses by calling a model through the Anthropic Messages API.

Needs the ANTHROPIC_API_KEY environment variable. Not used by the tests or CI,
which score saved responses so results are reproducible without a key.
"""
from __future__ import annotations

import csv
import os

import requests

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def ask(prompt: str, model: str, api_key: str, max_tokens: int = 500) -> str:
    resp = requests.post(
        API_URL,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    return "".join(b.get("text", "") for b in resp.json().get("content", []) if b.get("type") == "text")


def generate(cases: list, out_path: str, model: str = DEFAULT_MODEL, runs: int = 1) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY to use live mode.")
    rows = 0
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "id", "run", "response"])
        for case in cases:
            for run in range(1, runs + 1):
                w.writerow([model, case.id, run, ask(case.prompt, model, api_key)])
                rows += 1
    return rows
