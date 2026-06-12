from __future__ import annotations

from apply_patch import apply_patch_data
from pixel_art_core import validate_data


def test_valid_patch_changes_only_coordinates_and_revision(heart, clone):
    original = clone(heart)
    updated, errors = apply_patch_data(
        heart, {"base_revision": 1, "set": [{"x": 0, "y": 0, "color": 1}]}
    )
    assert not errors
    assert updated["revision"] == 2
    assert updated["pixels"][0][0] == "1"
    assert updated["canvas"] == original["canvas"]
    assert updated["palette"] == original["palette"]
    assert validate_data(updated).valid


def test_patch_is_atomic_on_out_of_bounds(heart):
    before = list(heart["pixels"])
    updated, errors = apply_patch_data(
        heart,
        {"base_revision": 1, "set": [{"x": 0, "y": 0, "color": 1}, {"x": 16, "y": 4, "color": 1}]},
    )
    assert updated is None
    assert any("out of bounds" in error for error in errors)
    assert heart["pixels"] == before


def test_patch_rejects_invalid_color_and_revision(heart):
    updated, errors = apply_patch_data(
        heart, {"base_revision": 2, "set": [{"x": 0, "y": 0, "color": 2}]}
    )
    assert updated is None
    assert any("Revision mismatch" in error for error in errors)
    assert any("Invalid color index" in error for error in errors)
