#!/usr/bin/env python3
"""Export a strict binary indexed artwork as an MSB-first C bitmap array."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pixel_art_core import atomic_write_text, validate_file


def c_identifier(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    if not value:
        value = "pixel_art"
    if value[0].isdigit():
        value = f"pixel_art_{value}"
    return value


def export_c_text(data: dict) -> str:
    if data["palette_limit"] != 2 or len(data["palette"]) != 2:
        raise ValueError("C bit-array export requires palette_limit=2 with exactly two palette entries.")
    identifier = c_identifier(data["name"])
    macro = identifier.upper()
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    bytes_per_row = (width + 7) // 8
    values = []
    for row in data["pixels"]:
        for offset in range(0, width, 8):
            bits = row[offset:offset + 8].ljust(8, "0")
            values.append(int(bits, 2))
    lines = []
    for row in range(height):
        start = row * bytes_per_row
        chunk = values[start:start + bytes_per_row]
        lines.append("    " + ", ".join(f"0x{value:02X}" for value in chunk) + ",")
    body = "\n".join(lines)
    return f"""#ifndef {macro}_H
#define {macro}_H

#include <stdint.h>

/* Row-major pixels: left-to-right, top-to-bottom, MSB first.
 * Each row is padded with zero bits to a complete byte.
 */
#define {macro}_WIDTH {width}
#define {macro}_HEIGHT {height}
#define {macro}_DATA_LENGTH {len(values)}

static const uint8_t {identifier}_data[{macro}_DATA_LENGTH] = {{
{body}
}};

#endif
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validation = validate_file(args.source)
    if not validation.valid:
        print("EXPORT FAILED")
        for error in validation.errors:
            print(f"- {error}")
        return 1
    try:
        text = export_c_text(validation.data)
    except ValueError as exc:
        print("EXPORT FAILED")
        print(f"- {exc}")
        return 1
    atomic_write_text(args.output, text)
    print("EXPORTED")
    print(f"Output: {Path(args.output)}")
    print("Layout: row-major, left-to-right, top-to-bottom, MSB first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
