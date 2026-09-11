"""套餐数据一致性测试（verify_plans 离线层）。

config.json 的套餐是性价比榜的地基：算术不自洽、档位额度反降这类硬伤
必须让 CI 红灯，而不是等榜单出错再回溯。时效/页面可达性属 WARN 级，
不在这里断言（见 scripts/verify_plans.py 与 plan-audit workflow）。
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import verify_plans as vp  # noqa: E402


def _load():
    return vp.load_plans()


def test_plans_have_valid_fields():
    """必填字段齐全、discount 在 (0,1]。"""
    errs = [e for p in _load() for e in vp.check_fields(p)]
    assert errs == []


def test_plans_arithmetic_consistent():
    """discount 与 monthly/implied_value(或 credit_value) 自洽（>5% 为硬伤）。"""
    errs = [e for p in _load() for e in vp.check_arithmetic(p)[0]]
    assert errs == []


def test_plan_families_monotonic():
    """同产品线月费升档时额度（implied_value/credit_value/tokens）非降。"""
    errs = vp.check_family_monotonic(_load())
    assert errs == []


def test_offline_audit_has_no_fail():
    """端到端：离线审计 0 FAIL（逐项断言已拆在上面，此为防回归兜底）。"""
    import datetime
    result = vp.audit(_load(), max_age_days=10**6,  # 时效层不影响本断言
                      today=datetime.date(2026, 9, 1), online=False)
    fails = [e for e in result["entries"] if e["status"] == "fail"]
    assert fails == []


def test_verify_plans_catches_dead_patterns():
    """当某个 plan 的 model_match 中包含无法命中任何模型的 pattern 时，必须报错 DEAD_PATTERN。"""
    bad_plan = {
        "name": "Test Plan With Dead Pattern",
        "monthly": 10.0,
        "discount": 0.5,
        "url": "https://example.com",
        "model_match": ["non_existent_model_12345*"],
    }
    errs = vp.check_dead_patterns([bad_plan])
    assert any("DEAD_PATTERN" in e for e in errs)

    # 正常 pattern 命中已有模型时无 DEAD_PATTERN 错误
    good_plan = {
        "name": "Test Plan With Valid Pattern",
        "monthly": 10.0,
        "discount": 0.5,
        "url": "https://example.com",
        "model_match": ["claude*"],
    }
    good_errs = vp.check_dead_patterns([good_plan])
    assert good_errs == []

    # 支持显式传入 registry_models（dict 列表或 str 列表）
    custom_errs = vp.check_dead_patterns([bad_plan], registry_models=["foo-model", "bar-model"])
    assert any("DEAD_PATTERN" in e for e in custom_errs)
    matched_errs = vp.check_dead_patterns([bad_plan], registry_models=[{"slug": "non_existent_model_123456"}])
    assert matched_errs == []

    # 集成到 audit 流程中，dead pattern 导致 fail 计数累加并记入 entry
    import datetime
    audit_res = vp.audit([bad_plan], max_age_days=10**6, today=datetime.date(2026, 9, 1), online=False)
    assert audit_res["summary"]["fail"] >= 1
    assert any(e["name"] == "Test Plan With Dead Pattern" and e["status"] == "fail" for e in audit_res["entries"])


def test_check_fields_allows_exclude_match():
    """check_fields 放行合法的 exclude_match，类型非法时报错。"""
    valid_plan = {
        "name": "Valid Exclude Plan",
        "monthly": 15.0,
        "discount": 0.3,
        "url": "https://example.com",
        "creator_match": ["OpenAI"],
        "exclude_match": ["*-mini", "*-preview"],
    }
    assert vp.check_fields(valid_plan) == []

    invalid_plan = dict(valid_plan, exclude_match="not-a-list")
    errs = vp.check_fields(invalid_plan)
    assert any("exclude_match 必须为列表" in e for e in errs)


def test_plan_params_preserves_exclude_match():
    """plan_params 正确提取并传递 exclude_match 列表。"""
    from pipeline.config import plan_params
    cfg = {
        "plans": [
            {
                "name": "Test Plan",
                "creator_match": ["OpenAI"],
                "exclude_match": ["gpt-4o-realtime*", "*-mini"],
                "monthly": 20.0,
                "discount": 0.5,
            }
        ]
    }
    parsed = plan_params(cfg)
    assert len(parsed) == 1
    assert parsed[0]["exclude_match"] == ["gpt-4o-realtime*", "*-mini"]


def test_coverage_matrix_bidirectional_pivot():
    """双向透视表正确生成正向透视、反向透视以及高亮未覆盖模型。"""
    plans = _load()
    matrix = vp.build_coverage_matrix(plans)
    assert "summary" in matrix
    assert "forward" in matrix
    assert "reverse" in matrix

    # 正向透视：聚合类套餐（model_match 非空）必须存在
    forward_names = {p["name"] for p in matrix["forward"]}
    assert "OpenCode Go" in forward_names
    assert "火山方舟 Coding Plan Pro" in forward_names

    # OpenCode Go 正向命中 muse-spark-1.3，scale 为 1.0
    opencode = next(p for p in matrix["forward"] if p["name"] == "OpenCode Go")
    opencode_hits = {h["slug"]: h for h in opencode["hits"]}
    assert "muse-spark-1.3" in opencode_hits
    assert opencode_hits["muse-spark-1.3"]["scale"] == 1.0
    assert abs(opencode_hits["muse-spark-1.3"]["effective_discount"] - 0.167) < 1e-4

    # 反向透视：高亮专栏必须精准识别未覆盖模型（muse-spark-1.1, inkling）
    uncovered_slugs = {u["slug"] for u in matrix["reverse"]["uncovered"]}
    assert "muse-spark-1.1" in uncovered_slugs
    assert "inkling" in uncovered_slugs

    # audit 字典完整包含 coverage 字段且原有结构毫发无损
    import datetime
    res = vp.audit(plans, max_age_days=10**6, today=datetime.date(2026, 9, 1), online=False)
    assert "coverage" in res
    assert res["summary"]["fail"] == 0

    # 验证控制台打印无报错
    vp.print_coverage_matrix(matrix)




