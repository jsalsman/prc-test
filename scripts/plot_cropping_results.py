"""Plot detection-rate curves for PRC cropping experiments."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from convert_base64 import encode_file

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "cropping"
TARGET_LEVELS = [1.0, 0.99, 0.95, 0.90]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot PRC cropping detection rates")
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        default=[
            RESULTS_DIR / "prc_cropping_results_512bits.csv",
            RESULTS_DIR / "prc_cropping_results_2500bits.csv",
        ],
        help="Aggregated detection CSVs (one per bit length)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory for plot outputs",
    )
    parser.add_argument(
        "--base64",
        action="store_true",
        help="Encode generated PNGs into .base64 and delete the original PNG",
    )
    return parser.parse_args()


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def threshold_marks(df: pd.DataFrame) -> Dict[float, int | None]:
    marks: Dict[float, int | None] = {}
    df_sorted = df.sort_values("keep_percentage", ascending=False)
    for level in TARGET_LEVELS:
        met = df_sorted[df_sorted["detection_rate"] >= level]
        marks[level] = int(met["keep_percentage"].min()) if not met.empty else None
    return marks


def plot_curve(df: pd.DataFrame, bit_length: int, output_dir: Path, use_base64: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"prc_cropping_summary_{bit_length}bits.png"

    keep = df["keep_percentage"].tolist()
    rates = df["detection_rate"].tolist()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(keep, rates, marker="o", label=f"{bit_length}-bit PRC watermark")
    ax.set_xlabel("Keep percentage (%)")
    ax.set_ylabel("Detection rate")
    ax.set_ylim(0, 1.05)
    ax.set_xlim(max(keep), min(keep))
    marks = threshold_marks(df)
    for level in TARGET_LEVELS:
        ax.axhline(level, color="gray", linestyle="--", linewidth=0.8)
        pct = marks[level]
        if pct is not None:
            ax.annotate(f">= {level:.2f} @ {pct}%", xy=(pct, level), xytext=(pct, level + 0.03))
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    plt.close(fig)

    if use_base64:
        encoded = encode_file(png_path, delete_original=True)
        return encoded
    return png_path


def main() -> None:
    args = parse_args()
    for path in args.inputs:
        df = load_results(path)
        if df.empty:
            print(f"[WARN] Skipping empty results: {path}")
            continue
        bit_length = int(df["bit_length"].iloc[0])
        encoded_path = plot_curve(df, bit_length, args.output_dir, args.base64)
        print(f"Wrote plot to {encoded_path}")


if __name__ == "__main__":
    main()
