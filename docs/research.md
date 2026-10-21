# HD map research

## Scope and source

Inventory source is the local `D:\Hope\Anomaly` installation. Its `changes152to153.txt` identifies it as Anomaly 1.5.3. `tools/extract_anomaly_resources.ps1` uses the game's own archive converter to read `configs.db0`, the UI global map, and texture archive thumbnail metadata. It extracts only the DDS files under `textures/map/` plus `textures/ui/ui_global_map.dds`; originals remain in a temporary working folder and are not committed.

## Findings

- `configs/game_maps_single.ltx` lists **34 configured location keys** and the global map. It defines global-map bounds in game coordinates; these values are recorded as metadata and are not altered.
- The texture archives contain **42 DDS files under `textures/map/`**, plus `textures/ui/ui_global_map.dds`. The 42 local textures account for 46,142,720 compressed source bytes.
- All 42 local map images use DXT3, have one base mip level, and range from 256×512 to 2048×2048. The global map is 1024×2048, DXT1, with one base mip level.
- Forty-one local textures match a configured location by normalized filename or the explicit Agroprom Underground alias. `map_aes_1.dds` remains included in the inventory but has no matching key in `level_maps_single`; its runtime use is unresolved.
- Some location keys have multiple map texture candidates (for example old and level-prefixed names). The manifest preserves all candidates and their configured `global_rect`; filename correspondence is recorded as a candidate and is not treated as proof of runtime binding.
- The level-map names and texture layout follow the X-Ray convention documented in the [X-Ray SDK map configuration reference](https://sdk.stalker-game.com/en/index.php?title=AI_Map_Compiling). Loose `gamedata` textures override archive assets as described by the [Anomaly Modding Book](https://github.com/TheParaziT/anomaly-modding-book/blob/main/docs/getting-started/main-folders-and-files.md).

## Upscale comparison and local build

`assets/manifest/maps.json` records all 42 local DDS assets and the global map, source archive/path, dimensions, format, mip levels, compressed size, candidate location association, and global rectangle. `tools/build_map_manifest.py` builds it from the local extraction.

Nearest, bicubic, and Lanczos 2× variants were compared on urban (`map_pripyat`), natural (`map_marsh`), and underground (`map_l04u_labx18`) maps. Their geometry and content remain at the same pixel-aligned locations; nearest keeps hard pixel steps, Lanczos looks slightly sharper, and bicubic gives the most balanced restrained result. Bicubic was selected to avoid overshoot and edge halos while preserving the source content; no neural model was used because it could hallucinate map details.

`tools/upscale_maps.py` produced all 43 outputs (42 local maps and the global map) in a temporary local MO2-ready tree. `tools/validate_map_build.py` passed coverage, 2× dimensions, aspect ratio, DDS format, mip count, output hashes, and global-bound checks. The output uses DXT3 for local maps and DXT1 for the global map, retains the source's one-mip layout, and totals 188,749,184 compressed bytes (~180 MiB); estimated mip-0 GPU storage is 188,743,680 bytes. These checks do not establish in-game performance or correctness of candidate runtime bindings.

Source maps are game assets. The public repository contains the extraction/upscale/build tooling and manifest only; users generate their own MO2 patch from their local installation unless redistribution permission is obtained.

## Next steps

1. Resolve `map_aes_1` usage and choose between duplicate candidate textures for each location using in-game rendering or stronger engine evidence.
2. Test the generated patch in Anomaly 1.5.3 with MO2, including local and global map display, zoom, performance, and marker alignment.
3. Capture comparison panels for a public README only if they can be shared without redistributing restricted source imagery; otherwise generate them locally for review.

## References

- [Anomaly addon template](https://github.com/sephellive/sephellive-anomaly-addon-template)
- [X-Ray SDK map configuration reference](https://sdk.stalker-game.com/en/index.php?title=AI_Map_Compiling)
- [Anomaly Modding Book: game folders and resources](https://github.com/TheParaziT/anomaly-modding-book/blob/main/docs/getting-started/main-folders-and-files.md)
