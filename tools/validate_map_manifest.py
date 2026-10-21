#!/usr/bin/env python3
"""Validate complete Anomaly 1.5.3 map metadata without requiring game assets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "assets/manifest/maps.json")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors: list[str] = []
    maps = data.get("maps", [])
    if data.get("game") != "S.T.A.L.K.E.R. Anomaly 1.5.3":
        errors.append("unexpected game version")
    if data.get("configured_location_count") != 34:
        errors.append("expected 34 configured location keys")
    if data.get("local_map_texture_count") != 42 or data.get("global_map_count") != 1:
        errors.append("expected 42 local maps and one global map")
    if len(maps) != 43:
        errors.append(f"expected 43 DDS records, found {len(maps)}")
    files: set[str] = set()
    unmatched: set[str] = set()
    for entry in maps:
        name = entry.get("technical_id", "<unnamed>")
        source = entry.get("source_file")
        if not source or source in files:
            errors.append(f"{name}: missing or duplicate source_file {source}")
        files.add(source)
        texture = entry.get("texture", {})
        if texture.get("width", 0) <= 0 or texture.get("height", 0) <= 0:
            errors.append(f"{name}: invalid dimensions")
        if texture.get("format") not in {"DXT1", "DXT3"} or texture.get("mip_levels") != 1:
            errors.append(f"{name}: unexpected source DDS format or mip count")
        if entry.get("mapping_status") == "unmatched_requires_review":
            unmatched.add(name)
    if unmatched != set(data.get("unmatched_assets", [])):
        errors.append("unmatched_assets list does not match per-map status")
    if data.get("runtime_location_bindings_confirmed") is not False:
        errors.append("runtime binding confirmation must reflect its current pending state")
    if errors:
        print("FAIL: " + "\nFAIL: ".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: 34 configured locations, 42 local maps, and one global map; unmatched: {sorted(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
