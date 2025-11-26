"""Utility to encode binary artifacts as base64 text and delete originals."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a binary file to <name>.base64")
    parser.add_argument("path", type=Path, help="Path to the binary file to encode")
    parser.add_argument(
        "--delete-original",
        action="store_true",
        help="Delete the source file after encoding (default: keep)",
    )
    return parser.parse_args()


def encode_file(path: Path, delete_original: bool = False) -> Path:
    encoded_path = path.with_suffix(path.suffix + ".base64")
    with path.open("rb") as f:
        encoded = base64.b64encode(f.read())
    with encoded_path.open("wb") as f:
        f.write(encoded)
    if delete_original:
        path.unlink()
    return encoded_path


def main() -> None:
    args = parse_args()
    if not args.path.exists():
        raise FileNotFoundError(args.path)
    out_path = encode_file(args.path, delete_original=args.delete_original)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
