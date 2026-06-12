#!/usr/bin/env python3
"""Atomically apply a coordinate patch to indexed pixel-art JSON."""

from __future__ import annotations

import argparse
import copy
import json
import sys

from pixel_art_core import atomic_write_text, load_json, validate_data, validate_file


def apply_patch_data(source: dict, patch: dict) -> tuple[dict | None, list[str]]:
    errors = []
    if patch.get("base_revision") != source.get("revision"):
        errors.append(
            f"Revision mismatch: source is {source.get('revision')}, patch expects {patch.get('base_revision')}."
        )
    operations = patch.get("set")
    if not isinstance(operations, list) or not operations:
        errors.append('Patch field "set" must be a non-empty array.')
        operations = []

    width = source["canvas"]["width"]
    height = source["canvas"]["height"]
    allowed = {entry["index"] for entry in source["palette"]}
    normalized = []
    for position, operation in enumerate(operations):
        if not isinstance(operation, dict):
            errors.append(f"Patch operation {position} must be an object.")
            continue
        x, y, color = operation.get("x"), operation.get("y"), operation.get("color")
        if not isinstance(x, int) or isinstance(x, bool) or not isinstance(y, int) or isinstance(y, bool):
            errors.append(f"Patch operation {position} must use integer x and y coordinates.")
            continue
        if not 0 <= x < width or not 0 <= y < height:
            errors.append(f"Coordinate out of bounds: x={x}, y={y}. Canvas is {width}x{height}.")
        if not isinstance(color, int) or isinstance(color, bool) or color not in allowed:
            errors.append(f"Invalid color index: {color}. Allowed indexes: {', '.join(map(str, sorted(allowed)))}.")
        normalized.append((x, y, color))
    if errors:
        return None, errors

    updated = copy.deepcopy(source)
    rows = [list(row) for row in updated["pixels"]]
    for x, y, color in normalized:
        rows[y][x] = str(color)
    updated["pixels"] = ["".join(row) for row in rows]
    updated["revision"] += 1
    validation = validate_data(updated)
    if not validation.valid:
        return None, [f"Patched document is invalid: {error}" for error in validation.errors]
    return updated, []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("patch")
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validation = validate_file(args.source)
    if not validation.valid:
        print("PATCH REJECTED")
        for error in validation.errors:
            print(f"- Source: {error}")
        return 1
    patch, errors = load_json(args.patch)
    if patch is None:
        print("PATCH REJECTED")
        for error in errors:
            print(f"- {error}")
        return 1
    updated, errors = apply_patch_data(validation.data, patch)
    if errors:
        print("PATCH REJECTED")
        for error in errors:
            print(f"- {error}")
        return 1
    atomic_write_text(args.output, json.dumps(updated, ensure_ascii=False, indent=2) + "\n")
    print("PATCH APPLIED")
    print(f"Revision: {validation.data['revision']} -> {updated['revision']}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
