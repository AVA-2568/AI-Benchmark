import os
import sys
import tempfile
from pathlib import Path
import pytest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 环境特定可写临时根目录（沙箱白名单目录，优先使用系统/沙箱通用可写临时目录）
_WRITABLE_ROOT = Path(tempfile.gettempdir()) / "pytest_tmp"


@pytest.fixture
def tmp_path(request):
    """覆盖内置 tmp_path fixture，确保在受控沙箱环境下使用受信任的可写路径。"""
    test_dir = _WRITABLE_ROOT / f"{request.node.name}_{os.getpid()}"
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
