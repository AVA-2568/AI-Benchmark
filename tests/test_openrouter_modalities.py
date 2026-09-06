"""Unit tests for OpenRouter modalities parsing, matching, and registry auditing."""
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from openrouter_modalities import (  # noqa: E402
    is_vision_model,
    find_openrouter_match,
    resolve_model_vision,
    audit_registry,
    load_openrouter_models,
)
from fetch_sources import FETCHERS  # noqa: E402


def test_is_vision_model():
    # 1. 明确包含 image input_modalities
    m1 = {
        "id": "test/model-vision",
        "architecture": {
            "modality": "text+image->text",
            "input_modalities": ["text", "image"],
        }
    }
    assert is_vision_model(m1) is True

    # 2. input_modalities 为空，但 modality 字符串含有 image
    m2 = {
        "id": "test/model-vision-2",
        "architecture": {
            "modality": "text+image+video->text",
            "input_modalities": [],
        }
    }
    assert is_vision_model(m2) is True

    # 3. 纯文本模型
    m3 = {
        "id": "test/model-text",
        "architecture": {
            "modality": "text->text",
            "input_modalities": ["text"],
        }
    }
    assert is_vision_model(m3) is False

    # 4. 边界与非法结构
    assert is_vision_model({}) is False
    assert is_vision_model(None) is False
    assert is_vision_model({"architecture": None}) is False


def test_find_openrouter_match():
    mock_or_models = [
        {
            "id": "anthropic/claude-3.5-sonnet",
            "architecture": {"modality": "text+image->text", "input_modalities": ["text", "image"]},
        },
        {
            "id": "qwen/qwen3.7-max",
            "architecture": {"modality": "text->text", "input_modalities": ["text"]},
        },
        {
            "id": "google/gemini-3.1-pro-preview",
            "architecture": {"modality": "text+image->text", "input_modalities": ["text", "image"]},
        },
    ]

    # 1. 精确命中
    entry1 = {"slug": "qwen3.7-max", "creator": "Qwen"}
    matched1 = find_openrouter_match(entry1, mock_or_models)
    assert matched1 is not None
    assert matched1["id"] == "qwen/qwen3.7-max"

    # 2. 前缀/preview 命中
    entry2 = {"slug": "gemini-3.1-pro", "creator": "Google"}
    matched2 = find_openrouter_match(entry2, mock_or_models)
    assert matched2 is not None
    assert matched2["id"] == "google/gemini-3.1-pro-preview"

    # 3. 未匹配
    entry3 = {"slug": "unknown-model-xyz", "creator": "None"}
    assert find_openrouter_match(entry3, mock_or_models) is None


def test_resolve_model_vision():
    mock_or_models = [
        {
            "id": "qwen/qwen3.7-max",
            "architecture": {"modality": "text->text", "input_modalities": ["text"]},
        },
        {
            "id": "openai/gpt-5.2-codex",
            "architecture": {"modality": "text+image->text", "input_modalities": ["text", "image"]},
        }
    ]

    # OpenRouter 权威判定为 False
    res_f, oid_f, src_f = resolve_model_vision({"slug": "qwen3.7-max", "creator": "Qwen"}, mock_or_models)
    assert res_f is False
    assert oid_f == "qwen/qwen3.7-max"
    assert src_f == "openrouter"

    # OpenRouter 权威判定为 True
    res_t, oid_t, src_t = resolve_model_vision({"slug": "gpt-5.2-codex", "creator": "OpenAI"}, mock_or_models)
    assert res_t is True
    assert oid_t == "openai/gpt-5.2-codex"
    assert src_t == "openrouter"

    # 未匹配模型走启发式
    res_vl, _, src_vl = resolve_model_vision({"slug": "my-new-vl-model"}, mock_or_models)
    assert res_vl is True
    assert src_vl == "heuristic"


def test_fetch_sources_registers_openrouter():
    assert "openrouter" in FETCHERS
    assert callable(FETCHERS["openrouter"])


def test_registry_has_zero_mismatches_with_openrouter():
    """验证当前的 model_registry.json 与缓存的 OpenRouter 模态完全一致。"""
    or_models = load_openrouter_models()
    if not or_models:
        pytest.skip("OpenRouter models cache not found (skipping in clean/offline environment)")
    report = audit_registry(or_models=or_models)
    assert report["mismatched_count"] == 0, f"Found mismatches: {report['mismatched']}"
