# AnomalyHope HD Maps

A reproducible 2× upscale pipeline for the complete Anomaly 1.5.3 PDA map texture set. The pipeline preserves source geometry and DDS compression family. It generates installable outputs locally from a user's game installation; source Anomaly textures are not redistributed by this repository.

## Requirements

- S.T.A.L.K.E.R. Anomaly 1.5.3 installed locally
- Python 3.11+ and Pillow
- DirectXTex `texconv.exe`
- Git LFS for any generated binary assets retained locally

## Build locally

Extract the needed configuration and map DDS resources from your installation:

```powershell
./tools/extract_anomaly_resources.ps1 -GamePath 'D:\Hope\Anomaly' -OutputPath "$env:TEMP\AnomalyHope-maps"
python ./tools/build_map_manifest.py --maps-root "$env:TEMP\AnomalyHope-maps\textures\map" --global-map "$env:TEMP\AnomalyHope-maps\textures\ui\ui_global_map.dds" --maps-ltx "$env:TEMP\AnomalyHope-maps\configs\configs\game_maps_single.ltx" --output ./assets/manifest/maps.json
python ./tools/upscale_maps.py --extracted-root "$env:TEMP\AnomalyHope-maps" --manifest ./assets/manifest/maps.json --output-root 'D:\AnomalyHope-HD-Maps-build' --texconv 'C:\Tools\texconv.exe'
python ./tools/validate_map_build.py --manifest ./assets/manifest/maps.json --output-root 'D:\AnomalyHope-HD-Maps-build'
```

The output root contains an MO2-ready `gamedata/` tree and a JSON build report. The tools do not write into the game installation. Review `docs/research.md` for source mapping, upscaler comparisons, size/memory estimates, and current testing limits.

## Status and distribution

The full 1.5.3 map inventory and a local 2× build have been produced and structurally validated. In-game PDA zoom, performance, and map rendering have not yet been verified. No public release is available. A release must not contain original game map textures without redistribution rights; use the local build workflow instead.

## License

The repository license covers only original project code and documentation, not Anomaly game assets.
