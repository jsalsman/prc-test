"""Aggregate PRC cropping raw detections into summary tables and thresholds."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "cropping"
TARGET_LEVELS = [1.0, 0.99, 0.95, 0.90]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate PRC cropping detection outputs")
    parser.add_argument(
        "--raw",
        nargs="+",
        type=Path,
        default=[
            RESULTS_DIR / "prc_cropping_raw_512bits.csv",
            RESULTS_DIR / "prc_cropping_raw_2500bits.csv",
        ],
        help="Raw detection CSV files to aggregate",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory for aggregated CSV outputs",
    )
    return parser.parse_args()


def load_raw(raw_paths: Iterable[Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in raw_paths:
        if path.exists():
            frames.append(pd.read_csv(path))
        else:
            print(f"[WARN] raw file missing: {path}")
    if not frames:
        raise FileNotFoundError("No raw detection CSVs were found")
    return pd.concat(frames, ignore_index=True)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["bit_length", "keep_percentage"], as_index=False)
        .agg(n_images=("detected", "size"), n_detected=("detected", "sum"))
    )
    grouped["detection_rate"] = grouped["n_detected"] / grouped["n_images"]
    return grouped.sort_values(["bit_length", "keep_percentage"], ascending=[True, False])


def thresholds(grouped: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    for bit_length, sub in grouped.groupby("bit_length"):
        sub_sorted = sub.sort_values("keep_percentage", ascending=False)
        for target in TARGET_LEVELS:
            achieved = sub_sorted[sub_sorted["detection_rate"] >= target]
            if not achieved.empty:
                threshold_pct = achieved["keep_percentage"].min()
            else:
                threshold_pct = None
            rows.append(
                {
                    "bit_length": bit_length,
                    "target_success_level": target,
                    "threshold_keep_percentage": threshold_pct,
                }
            )
    return pd.DataFrame(rows)


def write_outputs(agg: pd.DataFrame, thr: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for bit_length, sub in agg.groupby("bit_length"):
        out_path = output_dir / f"prc_cropping_results_{bit_length}bits.csv"
        sub.sort_values("keep_percentage", ascending=False).to_csv(out_path, index=False)
        print(f"Wrote {out_path}")
    thr_path = output_dir / "prc_cropping_thresholds.csv"
    thr.to_csv(thr_path, index=False)
    print(f"Wrote {thr_path}")


def main() -> None:
    args = parse_args()
    raw_df = load_raw(args.raw)
    agg = aggregate(raw_df)
    thr = thresholds(agg)
    write_outputs(agg, thr, args.output_dir)


if __name__ == "__main__":
    main()
