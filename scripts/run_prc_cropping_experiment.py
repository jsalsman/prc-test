"""Cropping + detection driver for PRC watermark robustness experiments.

This script stitches together cropping and detection runs by calling the
upstream PRC-Watermark CLI tools. It assumes you have already generated
watermarked images via `PRC-Watermark/encode.py` with a known `exp_id`.

Key responsibilities:
- Create deterministic central crops for several keep percentages.
- Invoke `decode.py` on each crop set and collect detection outcomes.
- Persist raw detection data into CSV files suitable for aggregation and plotting.

Example usage (512-bit experiment with default PRC settings):

```bash
python scripts/run_prc_cropping_experiment.py \
    --bit-length 512 \
    --test-num 200 \
    --exp-id prc_num_200_steps_50_fpr_1e-05_nowm_0
```

If you used non-default PRC settings (e.g., a different `--fpr`, `--inf_steps`,
`--method`, or `--prc_t`), pass matching arguments here so the script can
reconstruct the correct `exp_id` and call `decode.py` consistently.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
PRC_ROOT = ROOT / "PRC-Watermark"
RESULTS_DIR = ROOT / "results" / "cropping"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cropping + detection for PRC watermarking")
    parser.add_argument("--bit-length", type=int, default=512, help="Watermark message length (metadata only)")
    parser.add_argument("--test-num", type=int, required=True, help="Number of images encoded/decoded")
    parser.add_argument("--exp-id", type=str, help="Override experiment id (defaults to PRC naming convention)")
    parser.add_argument("--method", type=str, default="prc", help="Method passed to encode/decode (default: prc)")
    parser.add_argument("--inf-steps", type=int, default=50, help="Inference steps used during encode/decode")
    parser.add_argument("--fpr", type=float, default=0.00001, help="False positive rate used in PRC key generation")
    parser.add_argument("--nowm", type=int, default=0, help="Use non-watermarked latents (0/1) during encode")
    parser.add_argument("--prc-t", type=int, default=3, help="PRC sparsity parameter t used for KeyGen")
    parser.add_argument(
        "--keep-percentages",
        nargs="+",
        type=int,
        default=[100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
        help="Area percentages to retain during cropping",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory of original images; defaults to PRC-Watermark/results/<exp_id>/original_images",
    )
    parser.add_argument(
        "--skip-crop",
        action="store_true",
        help="Assume crop_* folders already exist and only run detection",
    )
    parser.add_argument(
        "--raw-out",
        type=Path,
        help="Where to write raw CSV (default results/cropping/prc_cropping_raw_<bit_length>bits.csv)",
    )
    parser.add_argument(
        "--decode-script",
        type=Path,
        default=PRC_ROOT / "decode.py",
        help="Path to upstream decode.py",
    )
    parser.add_argument(
        "--crop-metadata",
        type=Path,
        help="Optional path to save crop metadata from crop_images.py",
    )
    parser.add_argument(
        "--resize-back",
        dest="resize_back",
        action="store_true",
        help="Resize cropped patches back to original resolution before decoding",
    )
    parser.add_argument(
        "--no-resize-back",
        dest="resize_back",
        action="store_false",
        help="Skip resizing cropped patches back to original resolution",
    )
    parser.set_defaults(resize_back=True)
    return parser.parse_args()


def build_exp_id(args: argparse.Namespace) -> str:
    if args.exp_id:
        return args.exp_id
    return f"{args.method}_num_{args.test_num}_steps_{args.inf_steps}_fpr_{args.fpr}_nowm_{args.nowm}_bits_{args.bit_length}"_bits_{args.bit_length}


def call_cropper(
    input_dir: Path,
    output_root: Path,
    keep_percentages: Sequence[int],
    metadata_out: Path | None,
    resize_back: bool,
) -> None:
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "crop_images.py"),
        "--input-dir",
        str(input_dir),
        "--output-root",
        str(output_root),
        "--keep-percentages",
    ] + [str(p) for p in keep_percentages]
    if metadata_out:
        cmd += ["--metadata-out", str(metadata_out)]
    if resize_back:
        cmd.append("--resize-back")
    subprocess.run(cmd, check=True)


def run_decode(
    decode_script: Path,
    exp_id: str,
    keep_pct: int,
    args: argparse.Namespace,
) -> List[bool]:
    cmd = [
        sys.executable,
        str(decode_script),
        "--test_num",
        str(args.test_num),
        "--method",
        args.method,
        "--inf_steps",
        str(args.inf_steps),
        "--fpr",
        str(args.fpr),
        "--nowm",
        str(args.nowm),
        "--bits",

        str(args.bit_length),

        "--prc_t",
        str(args.prc_t),
        "--test_path",
        f"crop_{keep_pct}",
    ]
    subprocess.run(cmd, check=True, cwd=decode_script.parent)
    decoded_file = decode_script.parent / "decoded.txt"
    if not decoded_file.exists():
        raise FileNotFoundError(f"Expected decoded.txt at {decoded_file}")
    with decoded_file.open() as f:
        lines = [line.strip().lower() for line in f if line.strip()]
    results: List[bool] = []
    for line in lines:
        if line in {"true", "1", "yes"}:
            results.append(True)
        elif line in {"false", "0", "no"}:
            results.append(False)
        else:
            raise ValueError(f"Unrecognized detection output: {line}")
    return results


def ensure_raw_out(bit_length: int, raw_out: Path | None) -> Path:
    if raw_out:
        raw_out.parent.mkdir(parents=True, exist_ok=True)
        return raw_out
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    default_path = RESULTS_DIR / f"prc_cropping_raw_{bit_length}bits.csv"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return default_path


def write_raw_csv(
    raw_path: Path,
    bit_length: int,
    exp_id: str,
    args: argparse.Namespace,
    keep_pct: int,
    detections: Sequence[bool],
) -> None:
    is_new = not raw_path.exists()
    with raw_path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_id",
                "bit_length",
                "keep_percentage",
                "detected",
                "exp_id",
                "test_num",
                "fpr",
                "inf_steps",
                "method",
                "nowm",
                "prc_t",
                "test_path",
            ],
        )
        if is_new:
            writer.writeheader()
        for idx, detected in enumerate(detections):
            writer.writerow(
                {
                    "image_id": idx,
                    "bit_length": bit_length,
                    "keep_percentage": keep_pct,
                    "detected": int(bool(detected)),
                    "exp_id": exp_id,
                    "test_num": args.test_num,
                    "fpr": args.fpr,
                    "inf_steps": args.inf_steps,
                    "method": args.method,
                    "nowm": args.nowm,
                    "prc_t": args.prc_t,
                    "test_path": f"crop_{keep_pct}",
                }
            )


def main() -> None:
    args = parse_args()
    exp_id = build_exp_id(args)
    input_dir = args.input_dir or (PRC_ROOT / "results" / exp_id / "original_images")
    output_root = input_dir.parent

    if not args.skip_crop:
        call_cropper(
            input_dir=input_dir,
            output_root=output_root,
            keep_percentages=args.keep_percentages,
            metadata_out=args.crop_metadata,
            resize_back=args.resize_back,
        )

    raw_out = ensure_raw_out(args.bit_length, args.raw_out)
    for keep_pct in args.keep_percentages:
        detections = run_decode(args.decode_script, exp_id, keep_pct, args)
        if len(detections) != args.test_num:
            raise RuntimeError(
                f"Expected {args.test_num} detections for crop {keep_pct}, got {len(detections)}"
            )
        write_raw_csv(raw_out, args.bit_length, exp_id, args, keep_pct, detections)
        print(f"Processed keep {keep_pct}% -> {sum(detections)}/{len(detections)} detected")

    print(f"Raw detection data written to {raw_out}")


if __name__ == "__main__":
    main()
