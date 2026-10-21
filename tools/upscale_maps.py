#!/usr/bin/env python3
"""Generate a local MO2-ready 2x map override from a user's Anomaly install."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


def read_dds_header(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(128)
    if len(header) != 128 or header[:4] != b"DDS ":
        raise ValueError(f"Invalid DDS header: {path}")
    height, width = struct.unpack_from("<II", header, 12)
    mip_count = struct.unpack_from("<I", header, 28)[0] or 1
    fourcc = header[84:88].decode("ascii", errors="replace").rstrip("\0")
    return {
        "width": width,
        "height": height,
        "format": fourcc or "uncompressed",
        "mip_levels": mip_count,
        "bytes": path.stat().st_size,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compressed_mip0_bytes(info: dict[str, object]) -> int:
    block_bytes = 8 if info["format"] == "DXT1" else 16
    return ((int(info["width"]) + 3) // 4) * ((int(info["height"]) + 3) // 4) * block_bytes


def resize_premultiplied(source: Path, destination: Path, factor: int) -> tuple[int, int]:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    target_size = (image.width * factor, image.height * factor)
    # Premultiplied-alpha filtering avoids dark/bright fringes around transparent map edges.
    scaled = image.convert("RGBa").resize(target_size, Image.Resampling.BICUBIC)
    scaled.convert("RGBA").save(destination, format="PNG", optimize=False)
    return target_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extracted-root", type=Path, required=True,
                        help="Output directory from extract_anomaly_resources.ps1")
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "assets/manifest/maps.json")
    parser.add_argument("--output-root", type=Path, required=True,
                        help="New output directory to add to MO2 as a mod")
    parser.add_argument("--texconv", type=Path,
                        help="Path to DirectXTex texconv.exe; otherwise use PATH")
    parser.add_argument("--factor", type=int, choices=(2,), default=2,
                        help="Only the measured 2x pipeline is currently supported")
    args = parser.parse_args()

    extracted_root = args.extracted_root.resolve()
    output_root = args.output_root.resolve()
    if not extracted_root.is_dir():
        raise SystemExit(f"Extracted source directory does not exist: {extracted_root}")
    if output_root.exists():
        raise SystemExit(f"Output path must not already exist: {output_root}")
    texconv = str(args.texconv) if args.texconv else shutil.which("texconv")
    if not texconv or not Path(texconv).is_file():
        raise SystemExit("DirectXTex texconv.exe was not found; pass --texconv explicitly")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest["game"] != "S.T.A.L.K.E.R. Anomaly 1.5.3":
        raise SystemExit("The map manifest is not for Anomaly 1.5.3")
    output_root.mkdir(parents=True)
    report = {
        "game": manifest["game"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "method": "2x bicubic with premultiplied alpha",
        "factor": args.factor,
        "coordinate_transform": "(x, y) -> (2*x, 2*y); no crop or aspect-ratio change",
        "assets": [],
    }

    with tempfile.TemporaryDirectory(prefix="anomalyhope-map-build-") as temp_name:
        temp_root = Path(temp_name)
        for entry in manifest["maps"]:
            source = extracted_root / Path(entry["source_file"])
            if not source.is_file():
                raise SystemExit(f"Source asset is missing: {source}")
            input_info = read_dds_header(source)
            if input_info["width"] != entry["texture"]["width"] or input_info["height"] != entry["texture"]["height"]:
                raise SystemExit(f"Source dimensions differ from manifest: {source}")

            relative_output = Path("gamedata") / Path(entry["source_file"])
            destination_dir = output_root / relative_output.parent
            destination_dir.mkdir(parents=True, exist_ok=True)
            png_source = temp_root / f"{len(report['assets']):03d}_{source.stem}.png"
            output_size = resize_premultiplied(source, png_source, args.factor)
            expected_format = entry["texture"]["format"]
            if expected_format not in {"DXT1", "DXT3"}:
                raise SystemExit(f"Unsupported source format for {entry['technical_id']}: {expected_format}")
            command = [
                texconv,
                "-f", expected_format,
                "-m", "1",
                "-dx9",
                "-y",
                "-o", str(destination_dir),
                str(png_source),
            ]
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"texconv failed for {entry['technical_id']}:\n{completed.stdout}\n{completed.stderr}"
                )
            output_dds = destination_dir / f"{png_source.stem}.dds"
            expected_dds = destination_dir / source.name
            output_dds.replace(expected_dds)
            output_info = read_dds_header(expected_dds)
            if (output_info["width"], output_info["height"]) != output_size:
                raise RuntimeError(f"Unexpected output dimensions: {expected_dds}")
            if output_info["format"] != expected_format:
                raise RuntimeError(
                    f"Expected {expected_format}, got {output_info['format']}: {expected_dds}"
                )

            report["assets"].append({
                "technical_id": entry["technical_id"],
                "source_file": entry["source_file"],
                "output_file": str(relative_output).replace("\\", "/"),
                "locations": entry.get("locations_by_name_match", []),
                "mapping_status": entry.get("mapping_status"),
                "global_rect_from_ltx": entry.get("global_rect_from_ltx"),
                "source": {
                    **input_info,
                    "sha256": sha256_file(source),
                    "compressed_mip0_estimate_bytes": compressed_mip0_bytes(input_info),
                },
                "output": {
                    **output_info,
                    "sha256": sha256_file(expected_dds),
                    "compressed_mip0_estimate_bytes": compressed_mip0_bytes(output_info),
                },
            })

    report_path = output_root / "build_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(report['assets'])} map DDS overrides at 2x: {output_root}")
    print(f"Build report: {report_path}")


if __name__ == "__main__":
    main()
