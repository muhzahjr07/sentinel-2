# QGIS & ArcGIS Visualization Guide

This guide walks through loading, styling, and analyzing the generated mineral index GeoTIFFs within open-source GIS platforms (QGIS 3.x) and commercial suites (ArcGIS Pro).

---

## 1. Importing Output Rasters into QGIS

1. Launch **QGIS** (3.22+ recommended).
2. Set your Project CRS to **WGS 84 / UTM zone 44N (EPSG:32644)** (matching the Sentinel-2 native projection for Sri Lanka).
3. Drag and drop the generated GeoTIFF files from your output directory into the **Layers Panel**:
   - `favorability_S2.tif` (Targeting model)
   - `IOR.tif` (Iron oxide ratio)
   - `CR.tif` (Clay mineral ratio)
   - `bare_mask.tif` (Exposed gravel mask)
   - `RGB_TrueColor.tif` (Basemap reference)

---

## 2. Recommended Layer Styling & Symbology

### 2.1 Gemstone Favorability Model (`favorability_S2.tif`)
This layer represents standardized $Z$-scores. Values $> +1.5$ indicate significant positive mineral anomalies on exposed ground.

- **Render type**: `Singleband pseudocolor`
- **Color ramp**: `Spectral` (*Invert Color Ramp* so Red/Orange indicates high anomaly and Blue indicates low anomaly) or `Turbo`.
- **Min / Max Value Settings**:
  - Choose `Min / Max` under **Cumulative count cut** (e.g., `2.0%` to `98.0%`).
  - Mode: `Equal Interval` or `Continuous`.
  - Typical anomaly display range: `-1.0` to `+3.5`.
- **Layer Blending**: Set layer opacity to `85%` over `RGB_TrueColor.tif` or OpenStreetMap/Google Satellite basemaps.

---

### 2.2 Iron Oxide Ratio (`IOR.tif`)
Highlights lateritic capping, ferricrete, and iron-stained gem gravels.

- **Render type**: `Singleband pseudocolor`
- **Color ramp**: `YlOrRd` (Yellow-Orange-Red) or `Magma`.
- **Interpolation**: `Linear`.

---

### 2.3 Clay Minerals Ratio (`CR.tif`)
Pinpoints kaolinite, illite, and Al-OH hydrothermal alteration.

- **Render type**: `Singleband pseudocolor`
- **Color ramp**: `Viridis` or `Cividis`.
- **Contrast enhancement**: Stretch to Min/Max.

---

### 2.4 Bare Ground Mask (`bare_mask.tif`)
A binary raster ($1 = \text{Bare Soil / Placer Trap}$, $0 = \text{Vegetated / Water / Cloud}$).

- **Render type**: `Paletted/Unique values`.
- Click **Classify**:
  - Value `0`: Set **Opacity** to `0%` (transparent).
  - Value `1`: Set Color to vivid Cyan (`#00FFFF`) or Neon Yellow (`#FFFF00`) with `40%` opacity.

---

### 2.5 True Color Reference (`RGB_TrueColor.tif`)
A pre-scaled 3-band natural color GeoTIFF.

- **Render type**: `Multiband color`
- **Red band**: `Band 1 (Red - B04)`
- **Green band**: `Band 2 (Green - B03)`
- **Blue band**: `Band 3 (Blue - B02)`
- **Contrast enhancement**: `Stretch to Min/Max` or `None` (already pre-stretched during generation).

---

## 3. False Color Composites for Lithological Mapping

To visualize alteration zones in a single 3-band composite within QGIS:
1. Navigate to **Raster** &rarr; **Miscellaneous** &rarr; **Build Virtual Raster (VRT)**.
2. Select your individual aligned bands:
   - **Hydrothermal Alteration Composite**:
     - Band 1 (Red): `B12` ($2.19\,\mu\mathrm{m}$ - SWIR-2)
     - Band 2 (Green): `B11` ($1.61\,\mu\mathrm{m}$ - SWIR-1)
     - Band 3 (Blue): `B04` ($0.66\,\mu\mathrm{m}$ - Red)
   - Clays and altered rock formations will appear in distinct pastel cyan and yellow hues.

---

## 4. Exporting High-Priority Targets for Field Reconnaissance

1. In QGIS, use the **Raster Calculator** to isolate top-tier exploration targets:
   ```sql
   ("favorability_S2@1" >= 2.0) AND ("bare_mask@1" = 1)
   ```
2. Convert raster targets to polygons:
   - **Raster** &rarr; **Conversion** &rarr; **Polygonize (Raster to Vector)**.
3. Compute centroid coordinates (Latitude / Longitude).
4. Export as **KML** (for Google Earth) or **GPX** (for handheld Garmin GPS units) for ground-truthing in the field.
