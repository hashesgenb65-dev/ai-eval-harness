import pytest

from evalharness.core import (
    Case, check_consistency, check_format, evaluate, evaluate_response,
    load_cases, load_responses, term_present, FORBIDDEN_CONTENT, MISSING_FACT,
    TOO_LONG, FORMAT_VIOLATION, EMPTY,
)


def make_case(**kw):
    base = dict(id="T", category="t", prompt="p")
    base.update(kw)
    return Case(**base)


# ----------------------------------------------------------- term matching
def test_term_match_is_whole_word_and_case_insensitive():
    assert term_present("Au", "The symbol is au.")
    assert not term_present("Au", "because of this")


def test_alternatives_any_one_is_enough():
    case = make_case(must_include=[["17:05", "5:05"]])
    assert evaluate_response(case, "It arrives at 5:05 PM").passed
    assert not evaluate_response(case, "It arrives at 6:00 PM").passed


# ------------------------------------------------------------------ checks
def test_missing_fact_is_tagged():
    r = evaluate_response(make_case(must_include=[["Canberra"]]), "Sydney")
    assert not r.passed and r.tags == [MISSING_FACT]


def test_forbidden_content_fails_even_if_fact_present():
    case = make_case(must_include=[["red"]], must_not_include=["green"])
    r = evaluate_response(case, "red and green")
    assert not r.passed and FORBIDDEN_CONTENT in r.tags


def test_word_limit():
    case = make_case(max_words=3)
    assert evaluate_response(case, "one two three").passed
    r = evaluate_response(case, "one two three four")
    assert not r.passed and r.tags == [TOO_LONG]


def test_empty_response_scores_zero():
    r = evaluate_response(make_case(must_include=[["x"]]), "   ")
    assert r.score == 0 and r.tags == [EMPTY]


def test_score_is_partial_when_some_criteria_pass():
    case = make_case(must_include=[["a"]], max_words=2)
    r = evaluate_response(case, "a b c")   # accuracy ok (40), length fails (20)
    assert r.score == pytest.approx(66.7, abs=0.1)


# ----------------------------------------------------------------- formats
@pytest.mark.parametrize("fmt,text,ok", [
    ("json", '{"a": 1}', True),
    ("json", '```json\n{"a": 1}\n```', False),
    ("json", "not json", False),
    ("json", "[1, 2]", False),
    ("bullets:3", "- a\n- b\n- c", True),
    ("bullets:3", "- a\n- b", False),
    ("bullets", "no list here", False),
    ("numbered:2", "1. a\n2) b", True),
    ("one_sentence", "This is one sentence.", True),
    ("one_sentence", "One. Two.", False),
    ("number_only", " 102 ", True),
    ("number_only", "The answer is 102", False),
    ("", "anything", True),
])
def test_check_format(fmt, text, ok):
    assert check_format(fmt, text)[0] is ok


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        check_format("haiku", "text")


def test_format_violation_tag():
    r = evaluate_response(make_case(fmt="json"), "nope")
    assert r.tags == [FORMAT_VIOLATION]


# ------------------------------------------------------------- consistency
def test_consistency_flags_runs_that_disagree():
    case = make_case(must_include=[["yes"]])
    rows = [
        {"model": "m", "id": "T", "run": 1, "response": "yes"},
        {"model": "m", "id": "T", "run": 2, "response": "no"},
    ]
    results = evaluate([case], rows)
    (c,) = check_consistency(results)
    assert c.runs == 2 and c.outcomes_agree is False


def test_consistency_ignores_single_runs():
    case = make_case()
    results = evaluate([case], [{"model": "m", "id": "T", "run": 1, "response": "x"}])
    assert check_consistency(results) == []


def test_unknown_case_id_is_an_error():
    with pytest.raises(KeyError):
        evaluate([make_case()], [{"model": "m", "id": "ZZZ", "run": 1, "response": "x"}])


# ------------------------------------------------------- bundled data files
def test_bundled_data_loads_and_every_response_maps_to_a_case():
    cases = load_cases("data/test_cases.csv")
    responses = load_responses("data/sample_responses.csv")
    ids = {c.id for c in cases}
    assert len(cases) == 14
    assert {r["id"] for r in responses} <= ids
