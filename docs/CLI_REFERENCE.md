# Command-Line Interface (CLI) Reference Manual

This guide details the syntax, arguments, environment variables, and execution workflows for the two core processing utilities in this toolkit.

---

## 1. `download_sentinel2.py`

Handles authentication, catalogue queries, and stream-downloading from the **Copernicus Data Space Ecosystem (CDSE)**.

```bash
python download_sentinel2.py <command> [options]
```

### 1.1 `search` Command

Queries the CDSE OData catalogue for clear Sentinel-2 Level-2A (MSIL2A) scenes.

```bash
python download_sentinel2.py search [options]
```

#### Arguments & Flags:
| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--tile` | String | `None` | Sentinel-2 MGRS Tile (e.g., `44NKM`, `44NLM`, `44NMM`, `44NMK`). |
| `--location` | String | `ratnapura` | Preset Sri Lanka gem mining locality (e.g., `ratnapura`, `balangoda`, `elahera`, `kataragama`). Automatically resolves to corresponding MGRS tile if `--tile` is omitted. |
| `--max-cloud` | Float | `15.0` | Upper limit for scene cloud cover percentage. |
| `--limit` | Integer | `8` | Maximum number of candidate scenes to display. |
| `--start` | String | `None` | Filter start acquisition date in `YYYY-MM-DD` format. |
| `--end` | String | `None` | Filter end acquisition date in `YYYY-MM-DD` format. |

#### Example:
```bash
# Search for clear scenes (< 10% clouds) over Ratnapura in early 2026:
python download_sentinel2.py search --location ratnapura --max-cloud 10 --start 2026-01-01 --end 2026-03-31
```

---

### 1.2 `download` Command

Downloads the Sentinel-2 product archive (.zip) and optionally triggers the mineral index pipeline.

```bash
python download_sentinel2.py download --id <UUID> [options]
```

#### Arguments & Flags:
| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--id` | String | *Required* | Copernicus Product UUID obtained from the `search` command. |
| `--dest` | String | `.` | Target directory to store the downloaded `.zip` file. |
| `--user` | String | `None` | CDSE account username / registered email. |
| `--password` | String | `None` | CDSE account password. |
| `--process` | Flag | `False` | When specified, immediately feeds the downloaded file into `gem_exploration_indices.py`. |
| `--output-indices`| String | `output_S2` | Target folder for generated GeoTIFF rasters when `--process` is active. |

#### Authentication Environment Variables:
To avoid entering credentials on every run, export them in your terminal session:

```bash
# Linux / macOS
export CDSE_USER="your-email@example.com"
export CDSE_PASSWORD="your-secure-password"

# Windows PowerShell
$env:CDSE_USER = "your-email@example.com"
$env:CDSE_PASSWORD = "your-secure-password"
```

#### Example:
```bash
python download_sentinel2.py download \
  --id "7a9446f2-b8ec-4286-9a29-c454e99f6b9e" \
  --dest "./downloads" \
  --process \
  --output-indices "./indices_ratnapura"
```

---

## 2. `gem_exploration_indices.py`

Extracts bands from Sentinel-2 (.SAFE folder, extracted directory, or .zip archive) or ASTER band folders, aligns grids to 10m, and outputs exploration rasters.

```bash
python gem_exploration_indices.py <input_path> [options]
```

### Positional Argument:
- `input`: Path to Sentinel-2 `.SAFE` directory, uncompressed directory containing bands, `.zip` archive, or ASTER band folder.

### Options & Flags:
| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--output` | `-o` | String | `output_S2` | Directory where output GeoTIFF files will be written. |
| `--sensor` | | Choice | `s2` | Sensor type: `s2` (Sentinel-2 MSI) or `aster` (ASTER). |
| `--ndvi-threshold`| | Float | `0.30` | Maximum NDVI cutoff for bare soil and gravel placers. |

---

### Output Rasters Generated (Sentinel-2 Mode):

| File Name | Description | Data Type | Units / Range |
| :--- | :--- | :--- | :--- |
| `IOR.tif` | Iron Oxide Ratio ($B04/B02$) | Float32 | Ratio ($\ge 0$) |
| `NDII_Fe.tif` | Normalized Difference Iron Index | Float32 | $[-1.0, +1.0]$ |
| `CR.tif` | Clay Minerals Ratio ($B11/B12$) | Float32 | Ratio ($\ge 0$) |
| `NDCI.tif` | Normalized Difference Clay Index | Float32 | $[-1.0, +1.0]$ |
| `HI.tif` | Hydroxyl Alteration Index ($B11/B08$) | Float32 | Ratio ($\ge 0$) |
| `NDVI.tif` | Normalized Difference Vegetation Index | Float32 | $[-1.0, +1.0]$ |
| `bare_mask.tif` | Placer Soil Mask ($1 = \text{Bare}, 0 = \text{Other}$) | UInt8 | $\{0, 1\}$ |
| `favorability_S2.tif` | Masked Gemstone Favorability Model | Float32 | Standardized $Z$-score |
| `favorability_unmasked_S2.tif` | Unmasked Regional Favorability Model | Float32 | Standardized $Z$-score |
| `RGB_TrueColor.tif` | 3-Band Natural Color Composite (B04, B03, B02) | UInt8 (3 bands) | $[0, 255]$ |

---

### Examples:

#### 1. Processing Directly from a `.zip` Archive:
```bash
python gem_exploration_indices.py ./S2A_MSIL2A_20260215T045951_N0500_R119_T44NKM_20260215T083412.zip -o ./ratnapura_indices
```

#### 2. Tuning NDVI Threshold for Drier Seasons:
```bash
python gem_exploration_indices.py ./S2B_MSIL2A_...SAFE -o ./indices_dry --ndvi-threshold 0.25
```

#### 3. Processing ASTER Bands:
```bash
python gem_exploration_indices.py ./aster_bands/ -o ./output_aster --sensor aster
```
