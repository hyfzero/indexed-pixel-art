#!/usr/bin/env python3
"""Validate an indexed pixel-art JSON source."""

from __future__ import annotations

import argparse
import sys

from pixel_art_core import validate_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Pixel-art JSON source")
    parser.add_argument("--style-check", action="store_true", help="Report non-blocking style warnings")
    parser.add_argument(
        "--warn-isolated-pixels",
        action="store_true",
        help="Alias for style checking, retained for focused workflows",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_file(args.source, style_check=args.style_check or args.warn_isolated_pixels)
    if not result.valid:
        print("INVALID")
        for error in result.errors:
            print(f"- {error}")
        return 1

    data = result.data
    assert data is not None
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    print("VALID")
    print(f"Canvas: {width}x{height}")
    print(f"Palette entries: {len(data['palette'])}")
    print(f"Palette limit: {data['palette_limit']}")
    print(f"Transparency: {'enabled' if data['allow_transparency'] else 'disabled'}")
    print(f"Rows: {len(data['pixels'])}")
    print(f"Pixels per row: {width}")
    print(f"Total pixels: {width * height}")
    if result.warnings:
        print()
        print("STYLE WARNINGS")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
