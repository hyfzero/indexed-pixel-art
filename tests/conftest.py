from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def heart(root: Path) -> dict:
    return json.loads((root / "examples" / "binary-heart-16x16.json").read_text(encoding="utf-8"))


@pytest.fixture
def clone():
    return copy.deepcopy
