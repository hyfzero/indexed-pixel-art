from __future__ import annotations

from PIL import Image

from pixel_art_core import inspect_png, make_indexed_image
from render_pixel_art import render


def test_render_sizes_indexes_and_nearest_neighbor(root, tmp_path):
    source = root / "examples" / "binary-heart-16x16.json"
    output = tmp_path / "heart.png"
    rendered = render(str(source), str(output), preview_scale=8)
    with Image.open(output) as original, Image.open(rendered["preview"]) as preview:
        assert original.mode == "P"
        assert original.size == (16, 16)
        assert preview.size == (128, 128)
        assert set(original.tobytes()) == {0, 1}
        assert set(preview.tobytes()) == {0, 1}
        for y in range(16):
            for x in range(16):
                expected = original.getpixel((x, y))
                assert preview.getpixel((x * 8 + 4, y * 8 + 4)) == expected


def test_four_color_render_uses_at_most_four_indexes(root, tmp_path):
    output = tmp_path / "slime.png"
    render(str(root / "examples" / "four-color-slime-16x16.json"), str(output))
    with Image.open(output) as image:
        assert len(set(image.tobytes())) <= 4


def test_silhouette_preview(root, tmp_path):
    rendered = render(
        str(root / "examples" / "binary-cat-16x16.json"),
        str(tmp_path / "cat.png"),
        preview_scale=4,
        silhouette_preview=True,
    )
    with Image.open(rendered["silhouette"]) as image:
        assert image.size == (64, 64)
        assert set(image.tobytes()) <= {0, 1}


def test_inspection_rejects_wrong_size(heart, tmp_path):
    image = make_indexed_image(heart).resize((17, 16))
    path = tmp_path / "wrong-size.png"
    image.save(path)
    assert any("size mismatch" in error for error in inspect_png(path, heart)["errors"])


def test_inspection_rejects_extra_color(heart, tmp_path):
    image = make_indexed_image(heart)
    image.putpixel((0, 0), 2)
    path = tmp_path / "extra.png"
    image.save(path)
    assert any("undeclared palette index 2" in error for error in inspect_png(path, heart)["errors"])


def test_inspection_rejects_gray_palette_tampering(heart, tmp_path):
    image = make_indexed_image(heart)
    palette = image.getpalette()
    palette[3:6] = [127, 127, 127]
    image.putpalette(palette)
    path = tmp_path / "gray.png"
    image.save(path)
    assert any("color mismatch" in error for error in inspect_png(path, heart)["errors"])


def test_inspection_rejects_partial_alpha(heart, tmp_path):
    image = make_indexed_image(heart)
    image.info["transparency"] = bytes([255, 128] + [255] * 254)
    path = tmp_path / "alpha.png"
    image.save(path)
    assert any("partially transparent" in error for error in inspect_png(path, heart)["errors"])


def test_explicit_transparency_round_trip(heart, clone, tmp_path):
    data = clone(heart)
    data["allow_transparency"] = True
    data["transparent_index"] = 0
    image = make_indexed_image(data)
    path = tmp_path / "transparent.png"
    image.save(path)
    result = inspect_png(path, data)
    assert not result["errors"]
    assert result["transparency"] == 0
