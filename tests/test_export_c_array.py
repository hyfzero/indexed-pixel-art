from __future__ import annotations

import json

import pytest

from export_c_array import export_c_text


def test_binary_export_macros_and_bit_order(heart):
    text = export_c_text(heart)
    assert "#define BINARY_HEART_WIDTH 16" in text
    assert "#define BINARY_HEART_HEIGHT 16" in text
    assert "#define BINARY_HEART_DATA_LENGTH 32" in text
    assert "0x18, 0x18" in text
    assert "MSB first" in text


def test_non_byte_width_pads_each_row(heart, clone):
    data = clone(heart)
    data["name"] = "three-wide"
    data["canvas"] = {"width": 3, "height": 2}
    data["pixels"] = ["101", "010"]
    text = export_c_text(data)
    assert "#define THREE_WIDE_DATA_LENGTH 2" in text
    assert "0xA0," in text
    assert "0x40," in text


def test_four_color_export_is_rejected(root):
    data = json.loads((root / "examples" / "four-color-slime-16x16.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="palette_limit=2"):
        export_c_text(data)
