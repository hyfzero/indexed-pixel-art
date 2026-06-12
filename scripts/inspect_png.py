#!/usr/bin/env python3
"""Inspect an indexed PNG, optionally against its JSON source."""

from __future__ import annotations

import argparse
import sys

from pixel_art_core import inspect_png, validate_file


def format_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("png")
    parser.add_argument("--source")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = None
    if args.source:
        validation = validate_file(args.source)
        if not validation.valid:
            print("PNG INSPECTION FAILED")
            for error in validation.errors:
                print(f"- Source: {error}")
            return 1
        source = validation.data

    result = inspect_png(args.png, source)
    print("PNG INSPECTION")
    if "mode" in result:
        print(f"Mode: {result['mode']}")
        print(f"Size: {result['size'][0]}x{result['size'][1]}")
        declared = len(source["palette"]) if source else len(result.get("colors", {}))
        print(f"Declared palette entries: {declared}")
        print(f"Used palette indexes: {', '.join(map(str, result.get('used_indexes', [])))}")
        print("Used visible colors:")
        transparent = source.get("transparent_index") if source and source["allow_transparency"] else None
        for index, color in sorted(result.get("colors", {}).items()):
            suffix = " (transparent)" if index == transparent else ""
            print(f"- {index}: {format_hex(color)}{suffix}")
        print(f"Transparency: {'disabled' if result.get('transparency') is None else 'enabled'}")
    if result["errors"]:
        print("Constraint status: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
        return 1
    print("Constraint status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
