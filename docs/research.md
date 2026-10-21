# HD map research

**Status: preliminary.** This note defines the verified preparation work and constraints. The Anomaly 1.5.3 game archives and extracted map textures were not available during this pass, so the map inventory, original dimensions/formats, processing results, and geometric validation are still outstanding.

## Confirmed packaging and asset constraints

- Anomaly addons use loose resources under `gamedata/`; texture resources are DDS files and the loose tree mirrors paths inside packed game archives. See the [Anomaly Modding Book folder guide](https://github.com/TheParaziT/anomaly-modding-book/blob/main/docs/getting-started/main-folders-and-files.md).
- The provided addon template is configured to track `.dds` in Git LFS and creates release ZIPs containing only `gamedata/`. Its README warns not to grant rights to game assets or other material the publisher does not own. See [the template repository](https://github.com/sephellive/sephellive-anomaly-addon-template).
- The user's specification requires preserving map geometry and avoiding public redistribution of game textures without rights. This project will therefore use a local patch-generation workflow if the original map resources cannot be redistributed.

## Processing constraints

1. Inventory all location and global-map resources from the exact 1.5.3 installation, including underground maps; record source path, dimensions, DDS format, mip levels, byte size, and configuration references.
2. Compare candidate processing methods on one urban, one natural, and one underground map before choosing a pipeline. Upscaling is not evidence of recovered source detail; preserve the source content and avoid generated geometry.
3. Keep identical aspect ratio and map boundaries. Validate exact alignment with a 2x nearest-neighbor reference grid and difference/edge maps; any resampling must be documented and tested against marker placement.
4. Do not publish extracted original maps unless the asset license permits it. Prefer scripts that read user-supplied local sources and emit a MO2-ready patch archive.
5. Measure final DDS dimensions, format, mipmaps, compressed size, and GPU-memory implications before deciding whether 2x or 4x is appropriate.

## Required next research pass

- Obtain the user's local Anomaly 1.5.3 installation or extracted original resources.
- Enumerate every map image and all config references; generate a machine-readable map manifest with source dimensions and format.
- Identify representative test maps and compare at least two conservative processing methods plus the unmodified baseline.
- Establish the distributable-output policy based on game-asset rights before producing public binaries.

## Sources consulted

- [Anomaly Modding Book: main folders and files](https://github.com/TheParaziT/anomaly-modding-book/blob/main/docs/getting-started/main-folders-and-files.md)
- [Anomaly addon template](https://github.com/sephellive/sephellive-anomaly-addon-template)
