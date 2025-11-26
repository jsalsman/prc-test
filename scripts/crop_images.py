"""Central cropping utility for PRC watermark experiments.

This script crops every image in an input directory to several keep-percentages and
stores the results under separate subdirectories. It performs deterministic
center crops and optionally resizes the cropped patch back to the original size
(needed for PRC decode).

Example usage:

```
python scripts/crop_images.py \
    --input-dir PRC-Watermark/results/prc_num_200_steps_50_fpr_1e-05_nowm_0/original_images \
    --output-root PRC-Watermark/results/prc_num_200_steps_50_fpr_1e-05_nowm_0 \
    --keep-percentages 100 90 80 70 60 50 40 30 20 10 \
    --metadata-out results/cropping/crop_metadata_prc_num_200.csv
```
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, List

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Central cropping for PRC watermark images")
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory with original images")
    parser.add_argument(
        "--output-root", required=True, type=Path, help="Base directory where crop_* folders are written"
    )
    parser.add_argument(
        "--keep-percentages",
        nargs="+",
        type=int,
        default=[100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
        help="Area percentages to retain during cropping",
    )
    parser.add_argument(
        "--metadata-out",
        type=Path,
        help="Optional CSV path to log crop metadata (image_id, keep_percentage, dimensions)",
    )
    parser.add_argument(
        "--resize-back",
        dest="resize_back",
        action="store_true",
        help="Resize cropped patch back to the original resolution (recommended for PRC decode)",
    )
    parser.add_argument(
        "--no-resize-back",
        dest="resize_back",
        action="store_false",
        help="Skip resizing cropped patch to the original resolution",
    )
    parser.set_defaults(resize_back=True)
    parser.add_argument(
        "--image-suffix",
        default=".png",
        help="Image filename suffix to process (default: .png)",
    )
    return parser.parse_args()


def center_crop(image: Image.Image, keep_pct: int, resize_back: bool) -> Image.Image:
    assert 0 < keep_pct <= 100
    keep_fraction = keep_pct / 100.0
    scale = math.sqrt(keep_fraction)
    width, height = image.size
    crop_w = max(1, round(width * scale))
    crop_h = max(1, round(height * scale))
    left = (width - crop_w) // 2
    top = (height - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h
    cropped = image.crop((left, top, right, bottom))
    if resize_back:
        cropped = cropped.resize((width, height), Image.BICUBIC)
    return cropped


def iter_images(input_dir: Path, suffix: str) -> Iterable[Path]:
    yield from sorted(p for p in input_dir.iterdir() if p.is_file() and p.name.endswith(suffix))


def ensure_dirs(output_root: Path, keep_percentages: List[int]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for pct in keep_percentages:
        (output_root / f"crop_{pct}").mkdir(parents=True, exist_ok=True)


def write_metadata_row(writer, image_path: Path, keep_pct: int, width: int, height: int, crop_w: int, crop_h: int) -> None:
    writer.writerow(
        {
            "image_name": image_path.name,
            "keep_percentage": keep_pct,
            "orig_width": width,
            "orig_height": height,
            "crop_width": crop_w,
            "crop_height": crop_h,
        }
    )


def main() -> None:
    args = parse_args()
    input_dir: Path = args.input_dir
    output_root: Path = args.output_root
    keep_percentages: List[int] = args.keep_percentages
    resize_back: bool = args.resize_back
    suffix: str = args.image_suffix

    ensure_dirs(output_root, keep_percentages)
    metadata_file = None
    writer = None
    if args.metadata_out:
        args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
        metadata_file = args.metadata_out.open("w", newline="")
        writer = csv.DictWriter(
            metadata_file,
            fieldnames=[
                "image_name",
                "keep_percentage",
                "orig_width",
                "orig_height",
                "crop_width",
                "crop_height",
            ],
        )
        writer.writeheader()

    images = list(iter_images(input_dir, suffix))
    if not images:
        raise FileNotFoundError(f"No images ending with {suffix} found in {input_dir}")

    for image_path in images:
        with Image.open(image_path) as img:
            width, height = img.size
            for pct in keep_percentages:
                cropped = center_crop(img, pct, resize_back)
                if writer is not None:
                    crop_w, crop_h = cropped.size if not resize_back else (
                        round(width * math.sqrt(pct / 100.0)),
                        round(height * math.sqrt(pct / 100.0)),
                    )
                    write_metadata_row(writer, image_path, pct, width, height, crop_w, crop_h)
                dest = output_root / f"crop_{pct}" / image_path.name
                cropped.save(dest)

    if metadata_file:
        metadata_file.close()


if __name__ == "__main__":
    main()
