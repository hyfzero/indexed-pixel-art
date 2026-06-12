from __future__ import annotations

import pytest

from pixel_art_core import style_warnings, validate_data, validate_file


def test_valid_binary_and_four_color(root):
    assert validate_file(root / "examples" / "binary-heart-16x16.json").valid
    assert validate_file(root / "examples" / "four-color-slime-16x16.json").valid


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda d: d["pixels"].pop(), "Row count mismatch"),
        (lambda d: d["pixels"].append("0" * 16), "Row count mismatch"),
        (lambda d: d["pixels"].__setitem__(0, "0" * 15), "width mismatch"),
        (lambda d: d["pixels"].__setitem__(0, "0" * 17), "width mismatch"),
        (lambda d: d["canvas"].__setitem__("width", 0), "Canvas width"),
        (lambda d: d["canvas"].__setitem__("height", -1), "Canvas height"),
        (lambda d: d["pixels"].__setitem__(0, "2" + d["pixels"][0][1:]), "Invalid palette index"),
        (lambda d: d["palette"][1].__setitem__("index", 0), "Duplicate palette indexes"),
        (lambda d: d["palette"][1].__setitem__("hex", "#FFFFFF"), "Duplicate palette colors"),
        (lambda d: d["palette"][1].__setitem__("hex", "black"), "invalid hex"),
        (lambda d: d.__setitem__("palette_limit", 1), "exceed palette_limit"),
    ],
)
def test_invalid_inputs_report_precise_errors(heart, clone, mutation, message):
    data = clone(heart)
    mutation(data)
    result = validate_data(data)
    assert not result.valid
    assert any(message.lower() in error.lower() for error in result.errors)


def test_transparency_requires_declared_index(heart, clone):
    data = clone(heart)
    data["allow_transparency"] = True
    result = validate_data(data)
    assert any("transparent_index is required" in error for error in result.errors)


def test_transparency_is_valid_when_explicit(heart, clone):
    data = clone(heart)
    data["allow_transparency"] = True
    data["transparent_index"] = 0
    assert validate_data(data).valid


def test_binary_dithering_is_rejected(heart, clone):
    data = clone(heart)
    data["style"]["dithering"] = "checkerboard"
    result = validate_data(data)
    assert any("Binary mode" in error for error in result.errors)


def test_terminal_oled_requires_binary(heart, clone):
    data = clone(heart)
    data["palette_limit"] = 4
    data["style"]["preset"] = "terminal_oled"
    result = validate_data(data)
    assert any("terminal_oled" in error for error in result.errors)


def test_style_warnings_do_not_invalidate(heart, clone):
    data = clone(heart)
    data["pixels"][0] = "1000000000000000"
    result = validate_data(data, style_check=True)
    assert result.valid
    assert any("Isolated pixel" in warning for warning in result.warnings)
    assert any("touches canvas boundary" in warning for warning in result.warnings)


def test_vertical_symmetry_warning(heart, clone):
    data = clone(heart)
    data["style"]["symmetry"] = "vertical"
    data["pixels"][1] = "0100000000000000"
    warnings = style_warnings(data)
    assert any("Vertical symmetry differs" in warning for warning in warnings)


def test_gameboy_preset_is_valid(root):
    import json

    data = json.loads((root / "examples" / "four-color-slime-16x16.json").read_text(encoding="utf-8"))
    data["style"]["preset"] = "gameboy"
    data["style"]["shading"] = "clustered"
    data["style"]["dithering"] = "sparse_checkerboard"
    assert validate_data(data).valid


def test_hole_protrusion_and_visual_weight_warnings(heart, clone, root):
    import json

    cat = json.loads((root / "examples" / "binary-cat-16x16.json").read_text(encoding="utf-8"))
    assert any("single-pixel holes" in warning for warning in style_warnings(cat))

    data = clone(heart)
    data["pixels"] = ["0" * 16 for _ in range(16)]
    rows = [list(row) for row in data["pixels"]]
    for x, y in [(2, 1), (1, 2), (2, 2), (3, 2), (2, 3)]:
        rows[y][x] = "1"
    data["pixels"] = ["".join(row) for row in rows]
    warnings = style_warnings(data)
    assert any("edge protrusions" in warning for warning in warnings)
    assert any("off-center" in warning for warning in warnings)
