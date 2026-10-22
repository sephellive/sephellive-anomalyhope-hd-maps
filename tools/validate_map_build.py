#!/usr/bin/env python3
"""Validate a local map build's coverage, geometry, DDS headers, and files."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def header(path: Path) -> tuple[int, int, str, int]:
    with path.open("rb") as stream:
        data = stream.read(128)
    if len(data) != 128 or data[:4] != b"DDS ":
        raise ValueError(f"Invalid DDS file: {path}")
    height, width = struct.unpack_from("<II", data, 12)
    mips = struct.unpack_from("<I", data, 28)[0] or 1
    fourcc = data[84:88].decode("ascii", errors="replace").rstrip("\0")
    return width, height, fourcc or "uncompressed", mips


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "assets/manifest/maps.json")
    args = parser.parse_args()

    root = args.output_root.resolve()
    report_path = root / "build_report.json"
    if not report_path.is_file():
        raise SystemExit(f"Build report not found: {report_path}")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = {entry["technical_id"]: entry for entry in manifest["maps"]}
    actual = {entry["technical_id"]: entry for entry in report["assets"]}
    if expected.keys() != actual.keys():
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        raise SystemExit(f"Coverage mismatch; missing={missing}, extra={extra}")

    for technical_id, source_entry in expected.items():
        built = actual[technical_id]
        output = (root / Path(built["output_file"])).resolve()
        if root not in output.parents:
            raise SystemExit(f"Output escaped build root: {output}")
        if not output.is_file():
            raise SystemExit(f"Missing built file: {output}")
        width, height, fourcc, mips = header(output)
        source = source_entry["texture"]
        if (width, height) != (source["width"] * 2, source["height"] * 2):
            raise SystemExit(f"Dimensions are not exactly 2x for {technical_id}")
        if width * source["height"] != height * source["width"]:
            raise SystemExit(f"Aspect ratio changed for {technical_id}")
        if fourcc != source["format"]:
            raise SystemExit(f"DDS format changed for {technical_id}: {fourcc}")
        expected_mips = math.floor(math.log2(max(width, height))) + 1
        if mips != expected_mips:
            raise SystemExit(
                f"Unexpected mip chain for {technical_id}: {mips}; expected {expected_mips}"
            )
        if sha256_file(output) != built["output"]["sha256"]:
            raise SystemExit(f"Output hash does not match report for {technical_id}")
        if built["global_rect_from_ltx"] != source_entry.get("global_rect_from_ltx"):
            raise SystemExit(f"Global map coordinates changed for {technical_id}")

    print(f"PASS: {len(actual)} assets; dimensions 2x; full mip chains; aspect, DDS format, hash, and LTX bounds preserved.")
    print(f"Compressed DDS total: {sum(a['output']['bytes'] for a in actual.values()):,} bytes")
    print(f"Mip 0 GPU memory estimate: {sum(a['output']['compressed_mip0_estimate_bytes'] for a in actual.values()):,} bytes")


if __name__ == "__main__":
    main()
