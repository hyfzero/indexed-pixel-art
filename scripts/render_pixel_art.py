#!/usr/bin/env python3
"""Render validated indexed pixel art to PNG and nearest-neighbor previews."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from pixel_art_core import (
    atomic_save_image,
    inspect_png,
    make_indexed_image,
    style_warnings,
    validate_file,
)


def preview_path(output: Path, scale: int, silhouette: bool = False) -> Path:
    marker = "_silhouette_preview" if silhouette else "_preview"
    return output.with_name(f"{output.stem}{marker}_{scale}x{output.suffix}")


def make_silhouette(data: dict) -> Image.Image:
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    background = {0}
    if data["allow_transparency"]:
        background.add(data["transparent_index"])
    image = Image.new("P", (width, height))
    palette = [0] * (256 * 3)
    palette[0:3] = [255, 255, 255]
    palette[3:6] = [0, 0, 0]
    image.putpalette(palette)
    image.putdata([0 if int(char) in background else 1 for row in data["pixels"] for char in row])
    return image


def render(source: str, output: str, preview_scale: int = 8, silhouette_preview: bool = False) -> dict:
    result = validate_file(source, style_check=False)
    if not result.valid:
        raise ValueError("\n".join(result.errors))
    data = result.data
    assert data is not None
    if preview_scale < 1 or preview_scale > 64:
        raise ValueError("preview-scale must be in range 1..64.")

    output_path = Path(output)
    image = make_indexed_image(data)
    atomic_save_image(image, output_path, format="PNG", optimize=False)
    inspection = inspect_png(output_path, data)
    if inspection["errors"]:
        output_path.unlink(missing_ok=True)
        raise ValueError("Rendered PNG verification failed:\n" + "\n".join(inspection["errors"]))

    preview = image.resize(
        (image.width * preview_scale, image.height * preview_scale),
        Image.Resampling.NEAREST,
    )
    normal_preview = preview_path(output_path, preview_scale)
    atomic_save_image(preview, normal_preview, format="PNG", optimize=False)

    silhouette_path = None
    if silhouette_preview:
        silhouette = make_silhouette(data).resize(
            (image.width * preview_scale, image.height * preview_scale),
            Image.Resampling.NEAREST,
        )
        silhouette_path = preview_path(output_path, preview_scale, silhouette=True)
        atomic_save_image(silhouette, silhouette_path, format="PNG", optimize=False)

    return {
        "data": data,
        "output": output_path,
        "preview": normal_preview,
        "silhouette": silhouette_path,
        "inspection": inspection,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--output", required=True)
    parser.add_argument("--preview-scale", type=int, default=8)
    parser.add_argument("--silhouette-preview", action="store_true")
    parser.add_argument("--style-check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = render(args.source, args.output, args.preview_scale, args.silhouette_preview)
    except ValueError as exc:
        print("RENDER FAILED")
        for line in str(exc).splitlines():
            print(f"- {line}")
        return 1

    data = rendered["data"]
    inspection = rendered["inspection"]
    print("RENDERED")
    print(f"Source canvas: {data['canvas']['width']}x{data['canvas']['height']}")
    print(f"Original PNG: {rendered['output']}")
    print(f"Original PNG size: {inspection['size'][0]}x{inspection['size'][1]}")
    print(f"Preview PNG: {rendered['preview']}")
    print(f"Preview scale: {args.preview_scale}")
    if rendered["silhouette"]:
        print(f"Silhouette preview PNG: {rendered['silhouette']}")
    print(f"Verified palette entries: {len(data['palette'])}")
    print(f"Verified unique pixel indexes: {', '.join(map(str, inspection['used_indexes']))}")
    if args.style_check:
        warnings = style_warnings(data)
        if warnings:
            print()
            print("STYLE WARNINGS")
            for warning in warnings:
                print(f"- {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
