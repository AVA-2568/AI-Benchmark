"""Unit tests for pure helpers in score_aa / build (no network, no full pipeline)."""
import copy
import json
import os
import sys
from unittest import mock

import pytest

# scripts/ is not a package; put it on path for imports
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import build as build_mod  # noqa: E402
import score_aa as score  # noqa: E402
from pipeline.scoring import _weighted_total  # noqa: E402


# ---- to_float ----

@pytest.mark.parametrize("raw,expected", [
    ("1.5", 1.5),
    ("0", 0.0),
    ("-12.3", -12.3),
    ("", None),
    ("None", None),
    ("null", None),
    (None, None),
    ("  2.0  ", 2.0),
    ("abc", None),
])
def test_to_float(raw, expected):
    assert score.to_float(raw) == expected


# ---- norm ----

def test_norm_midpoint():
    assert score.norm(50, 0, 100) == 50.0


def test_norm_bounds():
    assert score.norm(0, 0, 100) == 0.0
    assert score.norm(100, 0, 100) == 100.0


def test_norm_flat_range():
    assert score.norm(7, 3, 3) == 50.0


def test_norm_clips_out_of_range():
    # 越界原始值必须裁剪到 [0, 100]，不得产生 >100 或 <0 的异常分
    assert score.norm(150, 0, 100) == 100.0
    assert score.norm(-50, 0, 100) == 0.0
    assert score.norm(2300, 800, 2200) == 100.0


# ---- _weighted_total ----

def test_weighted_total_no_discount_equals_plain():
    glob = {"a": 0.6, "b": 0.4}
    nrm = {"a": 80.0, "b": 60.0}
    assert _weighted_total(glob, nrm, set(), 1.0) == 0.6 * 80 + 0.4 * 60


def test_weighted_total_discount_downweights_imputed():
    glob = {"a": 0.6, "b": 0.4}
    nrm = {"a": 80.0, "b": 60.0}
    # b 为填补：权重 0.4 -> 0.2；a 真实 0.6；重归一化后总权重 0.8
    # total = (0.6*80 + 0.2*60) / 0.8 = 75.0
    assert _weighted_total(glob, nrm, {"b"}, 0.5) == 75.0


# ---- fmt_val ----

def test_fmt_val_plain():
    assert score.fmt_val(0.531, False, False) == "0.531"


def test_fmt_val_imputed():
    assert score.fmt_val(0.531, True, False) == "0.531*"


def test_fmt_val_low_beats_imputed():
    assert score.fmt_val(0.531, True, True) == "0.531**"


# ---- board_weights ----

def _load_config():
    path = os.path.join(_REPO, "config.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_board_weights_sum_to_one():
    cfg = _load_config()
    for bkey, board in cfg["leaderboards"].items():
        _, glob = score.board_weights(board)
        assert abs(sum(glob.values()) - 1.0) < 1e-9, bkey


def test_validate_config_ok():
    assert score.validate_config(_load_config()) is True


def test_validate_config_bad_cost_share():
    cfg = copy.deepcopy(_load_config())
    cfg["cost"]["input_share"] = 0.9
    cfg["cost"]["output_share"] = 0.2  # sum 1.1
    with pytest.raises(score.ConfigError, match="input_share"):
        score.validate_config(cfg)


def test_validate_config_bad_global_weights():
    cfg = copy.deepcopy(_load_config())
    # blow up a category weight so global sum != 1
    cfg["leaderboards"]["general"]["categories"][0]["weight"] = 0.99
    with pytest.raises(score.ConfigError, match="global weights"):
        score.validate_config(cfg)


def test_validate_config_metric_not_in_pool():
    cfg = copy.deepcopy(_load_config())
    cfg["imputation_pool"] = [
        m for m in cfg["imputation_pool"] if m != "HLE"
    ]
    with pytest.raises(score.ConfigError, match="not in imputation_pool"):
        score.validate_config(cfg)


def test_validate_config_rejects_bad_runtime_parameter():
    cfg = copy.deepcopy(_load_config())
    cfg["imputation"]["damping"] = 0
    with pytest.raises(score.ConfigError, match="damping"):
        score.validate_config(cfg)


def test_validate_config_rejects_non_http_plan_url():
    cfg = copy.deepcopy(_load_config())
    cfg["plans"][0]["url"] = "javascript:alert(1)"
    with pytest.raises(score.ConfigError, match="url must start with"):
        score.validate_config(cfg)


# ---- _replace_block ----

def test_replace_block_both_markers():
    txt = "A\n<!--FOO_START-->\nold\n<!--FOO_END-->\nB"
    out = build_mod._replace_block(txt, "FOO", "new")
    assert out == "A\n<!--FOO_START-->\nnew\n<!--FOO_END-->\nB"


def test_replace_block_missing_start_keeps_text():
    txt = "A\nold\n<!--FOO_END-->\nB"
    out = build_mod._replace_block(txt, "FOO", "new")
    assert out == txt


def test_replace_block_missing_end_keeps_text():
    txt = "A\n<!--FOO_START-->\nold\nB"
    out = build_mod._replace_block(txt, "FOO", "new")
    assert out == txt


# ---- build.main: stale / fresh control ----

def test_main_fails_on_stale_without_flag():
    with mock.patch.object(
        build_mod, "fetch_data", side_effect=build_mod.StaleCacheError("x")
    ):
        assert build_mod.main([]) == 1


def test_main_succeeds_fresh_and_records_stale_false():
    calls = {}

    def fake_write(stale, parser=None, offline=False):
        calls["stale"] = stale
        calls["offline"] = offline

    with mock.patch.object(build_mod, "fetch_data", return_value=(True, False)), \
         mock.patch.object(build_mod, "run"), \
         mock.patch.object(build_mod, "update_readme"), \
         mock.patch.object(build_mod, "_write_manifest", side_effect=fake_write):
        assert build_mod.main([]) == 0
    assert calls["stale"] is False
    assert calls["offline"] is False


def test_main_records_offline_flag():
    """--offline 复算缓存不应被误读为「本次联网抓取」。"""
    calls = {}

    def fake_write(stale, parser=None, offline=False):
        calls["stale"] = stale
        calls["offline"] = offline

    with mock.patch.object(build_mod, "fetch_data", return_value=(True, True)), \
         mock.patch.object(build_mod, "run"), \
         mock.patch.object(build_mod, "update_readme"), \
         mock.patch.object(build_mod, "_write_manifest", side_effect=fake_write):
        assert build_mod.main(["--offline"]) == 0
    assert calls["offline"] is True


def test_main_skips_readme_on_stale():
    readme_called = {"v": False}

    def fake_run(script, *args):
        pass

    def fake_readme():
        readme_called["v"] = True

    with mock.patch.object(build_mod, "fetch_data", return_value=(True, True)), \
         mock.patch.object(build_mod, "run", side_effect=fake_run), \
         mock.patch.object(build_mod, "update_readme", side_effect=fake_readme), \
         mock.patch.object(build_mod, "_write_manifest"):
        assert build_mod.main([]) == 0
    assert readme_called["v"] is False


def test_read_last_parser(tmp_path):
    marker = tmp_path / ".last_parser"
    marker.write_text("RSC stream", encoding="utf-8")
    with mock.patch.object(build_mod, "BASE", str(tmp_path)):
        assert build_mod._read_last_parser() == "RSC stream"


def test_read_last_parser_missing_returns_none(tmp_path):
    with mock.patch.object(build_mod, "BASE", str(tmp_path)):
        assert build_mod._read_last_parser() is None

