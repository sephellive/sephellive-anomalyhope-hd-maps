# AnomalyHope HD Maps

A conservative 2× restoration of every PDA map texture shipped with S.T.A.L.K.E.R. Anomaly 1.5.3: 42 local maps and the global Zone map. The pipeline preserves image bounds, aspect ratio, map coordinates, source compression family, and the original one-mip UI layout.

## Why the release is a local builder

The maps are Anomaly game assets. This repository and its GitHub releases contain the reproducible builder, inventory, and validators. They do not redistribute original or derived maps. The builder reads them from your installed copy and creates an independent MO2-ready add-on.

## Requirements

- S.T.A.L.K.E.R. Anomaly 1.5.3
- Python 3.11+ and Pillow
- DirectXTex `texconv.exe` available in `PATH`, or passed explicitly

## Build the MO2 add-on

From a release or repository checkout:

```powershell
python -m pip install -r requirements.txt
./tools/build_local.ps1 `
  -GamePath 'D:\Hope\Anomaly' `
  -OutputPath 'D:\Hope\mo2\mods\AnomalyHope HD Maps' `
  -ArchivePath 'D:\Hope\AnomalyHope-HD-Maps-v0.1.0.zip'
```

If `texconv.exe` is not in `PATH`, add `-TexconvPath 'C:\path\to\texconv.exe'`. The builder never writes into the game installation. Enable the output directory as a separate MO2 mod.

## Processing and verification

Local maps retain DXT3 and the global map retains DXT1. Premultiplied-alpha bicubic scaling avoids dark edge fringes and does not invent roads, buildings, paths, or geographic features. The result contains 43 DDS overrides and uses about 180 MiB of compressed mip-0 GPU storage.

The validators check inventory coverage, unique paths and IDs, exact 2× dimensions, aspect ratio, DDS format, mip count, hashes, and unchanged LTX bounds:

```powershell
python ./tools/validate_map_manifest.py
python ./tools/validate_map_build.py --output-root 'D:\Hope\mo2\mods\AnomalyHope HD Maps'
```

`map_aes_1.dds` is preserved because it exists in the base texture archive, although no direct key for it was found in `game_maps_single.ltx`. See [`docs/research.md`](docs/research.md) for details and current test limits.

## License

The repository license covers original project code and documentation only. It does not grant rights to S.T.A.L.K.E.R. Anomaly assets. Locally generated DDS files must not be redistributed without permission from the relevant rights holders.
