"""Unit tests for parse_aa.py pure functions.

The execution chain (parse -> sentinel -> CSV write) lives in ``main()``
and only runs when the module is invoked as a script, so importing
this module does NOT trigger network/file side effects. These tests
exercise the importable helpers directly.
"""
import os
import sys
import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import parse_aa  # noqa: E402


# ---- get() nested access ----

def test_get_simple():
    row = {"label": "GPT", "model": {"slug": "gpt", "creator": {"name": "OAI"}}}
    assert parse_aa.get(row, ("Model", "label")) == "GPT"
    assert parse_aa.get(row, ("Model Slug", "model", "slug")) == "gpt"
    assert parse_aa.get(row, ("Creator", "model", "creator", "name")) == "OAI"


def test_get_missing_path_returns_none():
    row = {"label": "X"}
    assert parse_aa.get(row, ("Model Slug", "model", "slug")) is None
    # non-dict intermediate -> None
    assert parse_aa.get(row, ("Label", "label", "deep")) is None


# ---- field_rates() / run_sentinel() ----

def _sentinel_row(label, all_filled=True):
    model = {
        f: (1.0 if all_filled else None)
        for f in parse_aa.SENTINEL_FIELDS
    }
    model["slug"] = label.lower()
    return {"label": label, "model": model}


def test_field_rates_full():
    rows = [_sentinel_row(f"M{i}") for i in range(900)]
    rates = parse_aa.field_rates(rows)
    assert set(rates) == set(parse_aa.SENTINEL_FIELDS)
    assert all(abs(v - 1.0) < 1e-9 for v in rates.values())


def test_field_rates_empty():
    rates = parse_aa.field_rates([])
    assert rates == {f: 0.0 for f in parse_aa.SENTINEL_FIELDS}


def test_run_sentinel_passes_on_full_data():
    rows = [_sentinel_row(f"M{i}") for i in range(900)]
    # should not raise; returns the rates dict
    rates = parse_aa.run_sentinel(rows)
    assert rates is not None


def test_run_sentinel_too_few_rows():
    rows = [_sentinel_row(f"M{i}") for i in range(10)]  # < MIN_ROWS
    try:
        parse_aa.run_sentinel(rows)
        assert False, "expected AssertionError for too-few rows"
    except AssertionError:
        pass


def test_run_sentinel_missing_field():
    # drop the 'label' key on one row -> sentinel should fire
    rows = [_sentinel_row(f"M{i}") for i in range(900)]
    del rows[0]["label"]
    try:
        parse_aa.run_sentinel(rows)
        assert False, "expected AssertionError for missing 'label'"
    except AssertionError:
        pass


def test_run_sentinel_disappeared_column():
    # one sentinel field entirely None -> below FIELD_RATE_MIN
    rows = [_sentinel_row(f"M{i}") for i in range(900)]
    for r in rows:
        r["model"]["terminalBench40"] = None
    with pytest.raises(AssertionError, match="字段哨兵触发"):
        parse_aa.run_sentinel(rows)


# ---- extract_via_rsc() ----

# _decode_rows_at is the real JSON-decoding primitive; it is pure
# (operates on a string), so we test it in-memory and avoid any
# temp-file I/O (the harness intercepts file deletion).

def _start(text):
    return text.index('"rows":[')


def test_decode_rows_at_parses_labeled():
    text = 'garbage "rows":[{"label":"A"},{"label":"B"}] trailing'
    rows = parse_aa._decode_rows_at(text, _start(text))
    assert rows is not None
    assert [r["label"] for r in rows] == ["A", "B"]


def test_decode_rows_at_returns_any_list_of_dicts():
    # label filtering happens in extract_via_rsc, not here
    text = '"rows":[{"x":1}]'
    rows = parse_aa._decode_rows_at(text, _start(text))
    assert rows == [{"x": 1}]


def test_decode_rows_at_invalid_json():
    text = '"rows":[not valid'
    assert parse_aa._decode_rows_at(text, _start(text)) is None


def test_decode_rows_at_list_of_non_dicts():
    # a JSON list, but elements are not dicts -> rejected
    text = '"rows":[1,2,3]'
    assert parse_aa._decode_rows_at(text, _start(text)) is None


def test_extract_via_rsc_missing_file():
    assert parse_aa.extract_via_rsc("/no/such/file.rsc") is None


# ---- build_cols() dynamic perf detection ----

def test_build_cols_detects_extra_perf():
    rows = [{
        "label": "A",
        "performance": {"medianOutputTokensPerSecond": 10, "weirdNew": 99},
    }]
    cols, extra = parse_aa.build_cols(rows)
    names = [c[0] for c in cols]
    assert "Median tok/s" in names
    assert extra == ["weirdNew"]
    # extra perf column appended with its raw key as both label and path
    assert ("weirdNew", "performance", "weirdNew") in cols
