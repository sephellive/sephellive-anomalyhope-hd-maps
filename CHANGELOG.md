# Changelog

## v0.2.0

- Replaced plain bicubic enlargement with the balanced `tactical-v3` pipeline.
- Added luminance-local contrast to separate roads, buildings and terrain.
- Added restrained warm-gray color grading to reduce the muddy blue cast.
- Added premultiplied-alpha Lanczos scaling and restrained detail recovery.
- Added full cubic-filtered mip chains to remove harsh zoomed-out aliasing.
- Preserved every source map's geometry, DDS family and LTX bounds.

## v0.1.0

- Added a one-command local builder for all 42 local maps and the global map.
- Added conservative 2× premultiplied-alpha bicubic processing with original DXT formats and map geometry preserved.
- Added coverage, unique-ID, dimensions, aspect ratio, DDS, hash, and LTX-bound validation.
- Added a release package that contains the legal local-generation toolkit rather than redistributed game textures.
