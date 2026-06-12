#!/usr/bin/env python3
"""Shared validation, rendering, inspection, and style logic."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "pixel-art.schema.json"
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@dataclass
class ValidationResult:
    data: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def load_json(path: str | Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        return None, [f"File not found: {path}."]
    except json.JSONDecodeError as exc:
        return None, [f"JSON parse error at line {exc.lineno}, column {exc.colno}: {exc.msg}."]
    except OSError as exc:
        return None, [f"Unable to read {path}: {exc}."]
    if not isinstance(value, dict):
        return None, ["Document root must be a JSON object."]
    return value, []


def _schema_errors(data: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"Schema error at {location}: {error.message}.")
    return errors


def validate_file(path: str | Path, style_check: bool = False) -> ValidationResult:
    data, errors = load_json(path)
    if data is None:
        return ValidationResult(errors=errors)
    return validate_data(data, style_check=style_check)


def validate_data(data: dict[str, Any], style_check: bool = False) -> ValidationResult:
    errors = _schema_errors(data)
    required = {
        "version", "name", "revision", "mode", "canvas", "palette_limit",
        "allow_transparency", "palette", "encoding", "pixels",
    }
    for key in sorted(required - data.keys()):
        errors.append(f"Missing required field: {key}.")

    if data.get("version") != "1.0":
        errors.append(f'Unsupported version: {data.get("version")!r}. Expected "1.0".')
    if data.get("mode") != "indexed":
        errors.append('Mode must be "indexed".')
    if data.get("encoding") != "matrix":
        errors.append('Encoding must be "matrix"; version 1.0 supports no other encoding.')

    canvas = data.get("canvas")
    width = canvas.get("width") if isinstance(canvas, dict) else None
    height = canvas.get("height") if isinstance(canvas, dict) else None
    if not isinstance(width, int) or isinstance(width, bool) or not 1 <= width <= 256:
        errors.append("Canvas width must be an integer in range 1..256.")
    if not isinstance(height, int) or isinstance(height, bool) or not 1 <= height <= 256:
        errors.append("Canvas height must be an integer in range 1..256.")

    limit = data.get("palette_limit")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        errors.append("palette_limit must be an integer in range 1..10.")

    palette = data.get("palette")
    indexes: list[int] = []
    hexes: list[str] = []
    if not isinstance(palette, list):
        errors.append("palette must be an array.")
        palette = []
    else:
        if isinstance(limit, int) and len(palette) > limit:
            errors.append(f"Palette entries exceed palette_limit: {len(palette)} > {limit}.")
        if len(palette) > 10:
            errors.append("Version 1.0 supports at most 10 palette entries (indexes 0..9).")
        for position, entry in enumerate(palette):
            if not isinstance(entry, dict):
                errors.append(f"Palette entry {position} must be an object.")
                continue
            index = entry.get("index")
            color = entry.get("hex")
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index <= 9:
                errors.append(f"Palette entry {position} has invalid index {index!r}; supported indexes are 0..9.")
            else:
                indexes.append(index)
            if not isinstance(color, str) or not HEX_RE.fullmatch(color):
                errors.append(f"Palette entry {position} has invalid hex {color!r}; expected #RRGGBB.")
            else:
                hexes.append(color.upper())
        duplicates = sorted({value for value in indexes if indexes.count(value) > 1})
        if duplicates:
            errors.append(f"Duplicate palette indexes: {', '.join(map(str, duplicates))}.")
        duplicate_hex = sorted({value for value in hexes if hexes.count(value) > 1})
        if duplicate_hex:
            errors.append(f"Duplicate palette colors: {', '.join(duplicate_hex)}.")
        if sorted(set(indexes)) != list(range(len(set(indexes)))):
            errors.append("Palette indexes must be continuous and start at 0.")

    allow_transparency = data.get("allow_transparency")
    transparent_index = data.get("transparent_index")
    if allow_transparency is True:
        if not isinstance(transparent_index, int) or isinstance(transparent_index, bool):
            errors.append("transparent_index is required when allow_transparency is true.")
        elif transparent_index not in indexes:
            errors.append(f"transparent_index {transparent_index} does not exist in the palette.")
    elif allow_transparency is False:
        if "transparent_index" in data:
            errors.append("transparent_index must not be present when allow_transparency is false.")
    else:
        errors.append("allow_transparency must be a boolean.")

    style = data.get("style", {})
    if isinstance(style, dict):
        outline_index = style.get("outline_index")
        if outline_index is not None and outline_index not in indexes:
            errors.append(f"style.outline_index {outline_index} does not exist in the palette.")
        preset = style.get("preset")
        if preset == "terminal_oled" and limit != 2:
            errors.append("terminal_oled preset requires palette_limit=2.")
        if limit == 2 and style.get("dithering", "disabled") != "disabled":
            errors.append("Binary mode requires style.dithering=disabled.")

    pixels = data.get("pixels")
    if not isinstance(pixels, list):
        errors.append("pixels must be an array.")
        pixels = []
    if isinstance(height, int) and len(pixels) != height:
        errors.append(f"Row count mismatch: expected {height} rows, received {len(pixels)}.")
    total = 0
    allowed = set(indexes)
    for y, row in enumerate(pixels):
        if not isinstance(row, str):
            errors.append(f"Row {y} must be a string.")
            continue
        total += len(row)
        if isinstance(width, int) and len(row) != width:
            errors.append(f"Row {y} width mismatch: expected {width} pixels, received {len(row)}.")
        for x, char in enumerate(row):
            if char < "0" or char > "9":
                errors.append(f"Invalid matrix character {char!r} at x={x}, y={y}; expected a digit 0..9.")
                continue
            index = int(char)
            if index not in allowed:
                allowed_text = ", ".join(map(str, sorted(allowed))) or "(none)"
                errors.append(
                    f'Invalid palette index "{char}" at x={x}, y={y}. Allowed indexes: {allowed_text}.'
                )
    if isinstance(width, int) and isinstance(height, int) and total != width * height:
        errors.append(f"Total pixel count mismatch: expected {width * height}, received {total}.")

    warnings = style_warnings(data) if style_check and not errors else []
    return ValidationResult(data=data, errors=_dedupe(errors), warnings=warnings)


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def palette_rgb(data: dict[str, Any]) -> dict[int, tuple[int, int, int]]:
    result = {}
    for entry in data["palette"]:
        value = entry["hex"].lstrip("#")
        result[entry["index"]] = tuple(int(value[offset:offset + 2], 16) for offset in (0, 2, 4))
    return result


def make_indexed_image(data: dict[str, Any]) -> Image.Image:
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    image = Image.new("P", (width, height))
    flat_palette = [0] * (256 * 3)
    for index, rgb in palette_rgb(data).items():
        flat_palette[index * 3:index * 3 + 3] = list(rgb)
    image.putpalette(flat_palette)
    image.putdata([int(char) for row in data["pixels"] for char in row])
    if data["allow_transparency"]:
        image.info["transparency"] = data["transparent_index"]
    return image


def inspect_png(path: str | Path, source: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"errors": []}
    try:
        with Image.open(path) as opened:
            opened.load()
            image = opened.copy()
            info = dict(opened.info)
    except (OSError, FileNotFoundError) as exc:
        return {"errors": [f"Unable to open PNG {path}: {exc}."]}

    result["mode"] = image.mode
    result["size"] = image.size
    if image.mode != "P":
        result["errors"].append(f"PNG mode mismatch: expected P, received {image.mode}.")
        return result

    pixel_indexes = list(image.tobytes())
    used = sorted(set(pixel_indexes))
    raw_palette = image.getpalette() or []
    colors = {}
    for index in used:
        offset = index * 3
        if offset + 2 >= len(raw_palette):
            result["errors"].append(f"PNG palette is missing data for used index {index}.")
            continue
        colors[index] = tuple(raw_palette[offset:offset + 3])
    transparency = info.get("transparency")
    result.update(used_indexes=used, colors=colors, transparency=transparency)

    if isinstance(transparency, bytes):
        alpha_values = set(transparency[index] if index < len(transparency) else 255 for index in used)
        if not alpha_values <= {0, 255}:
            result["errors"].append("PNG contains partially transparent palette entries.")
    elif transparency is not None and not isinstance(transparency, int):
        result["errors"].append("PNG contains unsupported transparency metadata.")

    if source is not None:
        expected_size = (source["canvas"]["width"], source["canvas"]["height"])
        if image.size != expected_size:
            result["errors"].append(f"PNG size mismatch: expected {expected_size[0]}x{expected_size[1]}, received {image.width}x{image.height}.")
        expected_colors = palette_rgb(source)
        for index in used:
            if index not in expected_colors:
                result["errors"].append(f"PNG uses undeclared palette index {index}.")
            elif colors.get(index) != expected_colors[index]:
                actual = colors.get(index)
                result["errors"].append(f"PNG color mismatch at index {index}: expected {expected_colors[index]}, received {actual}.")
        source_used = sorted({int(char) for row in source["pixels"] for char in row})
        if used != source_used:
            result["errors"].append(f"PNG used indexes {used} do not match source indexes {source_used}.")
        expected_pixels = [int(char) for row in source["pixels"] for char in row]
        if pixel_indexes != expected_pixels:
            result["errors"].append("PNG pixel indexes do not match the source matrix.")
        if source["allow_transparency"]:
            if transparency != source["transparent_index"]:
                result["errors"].append(
                    f"PNG transparent index mismatch: expected {source['transparent_index']}, received {transparency!r}."
                )
        elif transparency is not None:
            result["errors"].append("PNG contains transparency but the source disables it.")
    return result


def atomic_save_image(image: Image.Image, path: str | Path, **save_options: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=target.suffix, dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        image.save(temporary, **save_options)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=target.suffix, dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def style_warnings(data: dict[str, Any]) -> list[str]:
    rows = [[int(char) for char in row] for row in data["pixels"]]
    height = len(rows)
    width = len(rows[0]) if rows else 0
    background = {0}
    if data.get("allow_transparency"):
        background.add(data["transparent_index"])
    foreground = {(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value not in background}
    warnings: list[str] = []
    if not foreground:
        return ["No visible subject pixels found."]

    for x, y in sorted(foreground, key=lambda point: (point[1], point[0])):
        neighbors = {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}
        if not (neighbors & foreground):
            warnings.append(f"Isolated pixel detected at x={x}, y={y}.")
    boundary = sorted((x, y) for x, y in foreground if x in {0, width - 1} or y in {0, height - 1})
    if boundary:
        x, y = boundary[0]
        warnings.append(f"Subject touches canvas boundary at x={x}, y={y}.")

    holes = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (x, y) not in foreground and all(
                point in foreground for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            ):
                holes.append((x, y))
    if len(holes) >= 2:
        warnings.append(f"Multiple single-pixel holes detected: {len(holes)}.")

    protrusions = []
    for x, y in foreground:
        count = sum(point in foreground for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
        if count == 1:
            protrusions.append((x, y))
    if len(protrusions) >= max(3, len(foreground) // 8):
        x, y = sorted(protrusions, key=lambda point: (point[1], point[0]))[0]
        warnings.append(f"Possible irregular edge protrusions near x={x}, y={y}.")

    center_x = sum(x + 0.5 for x, _ in foreground) / len(foreground) / width
    center_y = sum(y + 0.5 for _, y in foreground) / len(foreground) / height
    if center_x < 0.30 or center_x > 0.70 or center_y < 0.30 or center_y > 0.70:
        warnings.append(f"Visual weight is strongly off-center (x={center_x:.2f}, y={center_y:.2f}).")

    symmetry = data.get("style", {}).get("symmetry")
    if symmetry in {"vertical", "approximate_vertical"}:
        mismatches = sum(rows[y][x] != rows[y][width - 1 - x] for y in range(height) for x in range(width // 2))
        threshold = 0 if symmetry == "vertical" else max(2, width * height // 32)
        if mismatches > threshold:
            warnings.append(f"Vertical symmetry differs at {mismatches} mirrored pixel pairs.")
    return _dedupe(warnings)
