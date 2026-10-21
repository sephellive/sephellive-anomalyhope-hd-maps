#!/usr/bin/env python3
"""Inventory Anomaly PDA map DDS files without copying game assets."""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

LOCATION_ALIASES = {
    "agroprom_underground": "l03u_agr_underground",
}


def dds_info(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(128)
    if len(header) != 128 or header[:4] != b"DDS ":
        raise ValueError(f"Not a valid DDS header: {path}")
    height, width = struct.unpack_from("<II", header, 12)
    mip_count = struct.unpack_from("<I", header, 28)[0]
    fourcc = header[84:88].decode("ascii", errors="replace").rstrip("\0")
    return {
        "width": width,
        "height": height,
        "format": fourcc or "uncompressed",
        "mip_levels": mip_count or 1,
        "bytes": path.stat().st_size,
    }


def read_map_config(path: Path) -> tuple[list[str], dict[str, str], str | None]:
    text = path.read_text(encoding="utf-8-sig")
    in_section = False
    names = []
    current_section = ""
    bounds: dict[str, str] = {}
    global_bounds = None
    for raw_line in text.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        section = re.fullmatch(r"\[([^]]+)\]", line)
        if section:
            current_section = section.group(1).strip().lower()
            in_section = current_section == "level_maps_single"
            continue
        if in_section:
            match = re.match(r"^([a-zA-Z0-9_]+)\s*=", line)
            if match:
                names.append(match.group(1).lower())
        else:
            match = re.match(r"^global_rect\s*=\s*(.+)$", line, re.I)
            if match:
                if current_section == "global_map":
                    global_bounds = match.group(1).strip()
                elif current_section:
                    bounds[current_section] = match.group(1).strip()
    return names, bounds, global_bounds


def normalize_location(name: str) -> str:
    name = name.lower()
    return re.sub(r"^(?:l\d{2}|k\d{2})_", "", name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps-root", type=Path, required=True,
                        help="Extracted gamedata/textures/map directory")
    parser.add_argument("--global-map", type=Path, required=True,
                        help="Extracted textures/ui/ui_global_map.dds")
    parser.add_argument("--maps-ltx", type=Path, required=True,
                        help="Extracted configs/game_maps_single.ltx")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    levels, location_bounds, global_bounds = read_map_config(args.maps_ltx)
    if not levels:
        raise SystemExit("No entries found in [level_maps_single]")
    records = []
    map_files = sorted(args.maps_root.glob("*.dds"))
    if not map_files:
        raise SystemExit(f"No map DDS files found under {args.maps_root}")

    for path in map_files:
        asset_id = path.stem.split("#", 1)[0]
        name = asset_id.removeprefix("map_")
        normalized = normalize_location(name)
        locations = [level for level in levels
                     if normalize_location(level) == normalized]
        if not locations and normalized in LOCATION_ALIASES:
            locations = [LOCATION_ALIASES[normalized]]
            mapping_status = "known_name_alias"
        else:
            mapping_status = "name_match" if locations else "unmatched_requires_review"
        records.append({
            "technical_id": path.stem,
            "source_file": f"textures/map/{path.name}",
            "source_archive": "db/textures/textures.db2",
            "locations_by_name_match": locations,
            "mapping_status": mapping_status,
            "global_rect_from_ltx": {
                level: location_bounds[level]
                for level in locations
                if level in location_bounds
            } or None,
            "texture": dds_info(path),
            "output_file": None,
            "processing_status": "not_started",
            "geometry_verification": "pending",
        })

    records.append({
        "technical_id": "global_map",
        "source_file": "textures/ui/ui_global_map.dds",
        "source_archive": "db/textures/textures_ui.db0",
        "locations_by_name_match": levels,
        "mapping_status": "global_map",
        "texture": dds_info(args.global_map),
        "global_bounds_from_ltx": global_bounds,
        "output_file": None,
        "processing_status": "not_started",
        "geometry_verification": "pending",
    })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({
            "schema_version": 1,
            "game": "S.T.A.L.K.E.R. Anomaly 1.5.3",
            "inventory_basis": [
                "configs/game_maps_single.ltx:[level_maps_single]",
                "textures/map/*.dds",
                "textures/ui/ui_global_map.dds",
            ],
            "configured_location_count": len(levels),
            "local_map_texture_count": len(records) - 1,
            "global_map_count": 1,
            "local_texture_directory_inventory_complete": True,
            "runtime_location_bindings_confirmed": False,
            "unmatched_assets": [
                m["technical_id"] for m in records[:-1]
                if m["mapping_status"] == "unmatched_requires_review"
            ],
            "notes": [
                "Game DDS assets were read locally; this manifest contains metadata and paths only.",
                "Unmatched textures are retained for manual review rather than omitted.",
                "Name matching is a candidate association, not proof of runtime binding.",
            ],
            "maps": records,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Configured locations: {len(levels)}")
    print(f"Local map textures: {len(map_files)}")
    print(f"Unmatched filenames: {sum(not m['locations_by_name_match'] for m in records[:-1])}")
    print(f"Wrote inventory to {args.output}")


if __name__ == "__main__":
    main()
