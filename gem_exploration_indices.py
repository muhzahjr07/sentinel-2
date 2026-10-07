#!/usr/bin/env python3
"""
Sentinel-2 Gemstone Exploration Spectral Indices & Favorability Generator
Tailored for Sri Lankan gem exploration (Ratnapura, Elahera, Balangoda, etc.)

Author: Antigravity AI & Geospatial Toolkit
"""

import os
import sys
import zipfile
import argparse
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

# SCL (Scene Classification Layer) values in Sentinel-2 L2A:
# 0: NO_DATA, 1: SATURATED, 2: DARK_AREA, 3: CLOUD_SHADOWS
# 4: VEGETATION, 5: NOT_VEGETATED (Bare soil/sand/gravel), 6: WATER
# 7: UNCLASSIFIED, 8: CLOUD_MED, 9: CLOUD_HIGH, 10: CIRRUS, 11: SNOW


def find_sentinel2_bands(input_path):
    """
    Locates required bands inside a .SAFE folder, extracted directory, or .zip archive.
    Required bands: B02, B03, B04, B08 (10m), B11, B12 (20m), optional SCL (20m).
    """
    is_zip = False
    prefix = ""

    if os.path.isfile(input_path) and input_path.lower().endswith(".zip"):
        is_zip = True
        prefix = f"/vsizip/{os.path.abspath(input_path)}/"
        with zipfile.ZipFile(input_path, 'r') as z:
            all_files = [f.replace('\\', '/') for f in z.namelist()]
    elif os.path.isdir(input_path):
        all_files = []
        for root, _, files in os.walk(input_path):
            for f in files:
                rel_p = os.path.relpath(os.path.join(root, f), input_path).replace('\\', '/')
                all_files.append(rel_p)
        prefix = os.path.abspath(input_path) + "/"
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    band_targets = {
        'B02': ['_B02_10m', '_B02', 'B02'],
        'B03': ['_B03_10m', '_B03', 'B03'],
        'B04': ['_B04_10m', '_B04', 'B04'],
        'B08': ['_B08_10m', '_B08', 'B08'],
        'B11': ['_B11_20m', '_B11', 'B11'],
        'B12': ['_B12_20m', '_B12', 'B12'],
        'SCL': ['_SCL_20m', '_SCL', 'SCL'],
    }

    found_bands = {}

    for b_name, patterns in band_targets.items():
        matched = None
        for pat in patterns:
            candidates = [
                f for f in all_files
                if (f.lower().endswith('.jp2') or f.lower().endswith('.tif') or f.lower().endswith('.tiff'))
                and (f"_{pat}." in f or f"/{pat}." in f or f"{pat}_" in f or pat in os.path.basename(f).split('.')[0].split('_'))
            ]
            if candidates:
                if b_name in ['B02', 'B03', 'B04', 'B08']:
                    ranked = sorted(candidates, key=lambda x: (0 if 'R10m' in x else 1, 0 if x.endswith('.jp2') else 1))
                elif b_name in ['B11', 'B12', 'SCL']:
                    ranked = sorted(candidates, key=lambda x: (0 if 'R20m' in x else 1, 0 if x.endswith('.jp2') else 1))
                else:
                    ranked = candidates
                matched = ranked[0]
                break
        
        if matched:
            found_bands[b_name] = prefix + matched if is_zip else os.path.join(input_path, matched)

    required = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
    missing = [b for b in required if b not in found_bands]
    if missing:
        raise FileNotFoundError(
            f"Could not find required Sentinel-2 bands {missing} in {input_path}.\n"
            f"Total files searched: {len(all_files)}"
        )

    return found_bands


def resample_and_read(src_path, ref_meta, ref_shape, resampling=Resampling.bilinear):
    """
    Reads a raster band and reprojects/resamples it directly into the reference grid.
    """
    with rasterio.open(src_path) as src:
        src_data = src.read(1)
        src_crs = src.crs
        src_transform = src.transform
        src_nodata = src.nodata

    dst_data = np.empty(ref_shape, dtype='float32')
    
    reproject(
        source=src_data.astype('float32'),
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=ref_meta['transform'],
        dst_crs=ref_meta['crs'],
        dst_nodata=np.nan,
        resampling=resampling
    )
    return dst_data


def compute_sentinel2_indices(input_path, out_dir, ndvi_bare_thresh=0.30, apply_baseline_offset=True):
    """
    Main processing pipeline for Sentinel-2 L2A Gemstone Exploration Indices.
    """
    os.makedirs(out_dir, exist_ok=True)
    print(f"[*] Scanning for Sentinel-2 bands in: {input_path}")
    bands = find_sentinel2_bands(input_path)
    
    for b, p in bands.items():
        print(f"    - {b}: {os.path.basename(p)}")

    ref_band_path = bands['B04']
    with rasterio.open(ref_band_path) as ref:
        ref_meta = ref.meta.copy()
        ref_shape = ref.shape

    print(f"[*] Reference grid defined by B04 (10m): {ref_shape[1]}x{ref_shape[0]} px, CRS: {ref_meta.get('crs')}")

    # Read and align bands to 10m grid
    print("[*] Reading and aligning 10m and 20m bands to reference grid...")
    b2 = resample_and_read(bands['B02'], ref_meta, ref_shape, Resampling.bilinear)
    b3 = resample_and_read(bands['B03'], ref_meta, ref_shape, Resampling.bilinear)
    b4 = resample_and_read(bands['B04'], ref_meta, ref_shape, Resampling.bilinear)
    b8 = resample_and_read(bands['B08'], ref_meta, ref_shape, Resampling.bilinear)
    b11 = resample_and_read(bands['B11'], ref_meta, ref_shape, Resampling.bilinear)
    b12 = resample_and_read(bands['B12'], ref_meta, ref_shape, Resampling.bilinear)

    # Read SCL if available (categorical: use nearest neighbor!)
    scl_data = None
    if 'SCL' in bands:
        print("[*] Reading Scene Classification Layer (SCL) for cloud/water/shadow filtering...")
        scl_data = resample_and_read(bands['SCL'], ref_meta, ref_shape, Resampling.nearest)

    # Handle Sentinel-2 Processing Baseline >= 04.00 BOA offset
    if apply_baseline_offset:
        valid_b4 = b4[b4 > 0]
        if len(valid_b4) > 0 and np.nanpercentile(valid_b4, 1) >= 950:
            print("[*] Detected Processing Baseline >= 04.00 (1000 DN offset detected). Correcting BOA offset...")
            b2 = np.maximum(0.0, b2 - 1000.0)
            b3 = np.maximum(0.0, b3 - 1000.0)
            b4 = np.maximum(0.0, b4 - 1000.0)
            b8 = np.maximum(0.0, b8 - 1000.0)
            b11 = np.maximum(0.0, b11 - 1000.0)
            b12 = np.maximum(0.0, b12 - 1000.0)

    # Convert to reflectance (0.0 to 1.0)
    b2 /= 10000.0
    b3 /= 10000.0
    b4 /= 10000.0
    b8 /= 10000.0
    b11 /= 10000.0
    b12 /= 10000.0

    eps = 1e-6

    # Valid data mask (not zero or NaN)
    valid_mask = (b2 > 0) & (b3 > 0) & (b4 > 0) & (b8 > 0) & (b11 > 0) & (b12 > 0)
    valid_mask &= ~np.isnan(b2) & ~np.isnan(b4) & ~np.isnan(b8) & ~np.isnan(b11) & ~np.isnan(b12)

    # Cloud & Shadow exclusion using SCL if present
    if scl_data is not None:
        clear_sky_mask = ~np.isin(scl_data.astype(int), [0, 1, 3, 8, 9, 10])
        valid_mask &= clear_sky_mask

    print("[*] Computing spectral indices...")
    # 1. Iron Oxide Ratio (IOR) = B04 / B02 (staining in saprolite & gem gravels)
    ior = np.where(valid_mask, b4 / (b2 + eps), np.nan)

    # 2. Normalized Difference Iron Index (NDII_Fe) = (B04 - B02) / (B04 + B02)
    ndii_fe = np.where(valid_mask, (b4 - b2) / (b4 + b2 + eps), np.nan)

    # 3. Clay Minerals Ratio (CR) = B11 / B12 (Al-OH absorption at 2.2um)
    cr = np.where(valid_mask, b11 / (b12 + eps), np.nan)

    # 4. Normalized Difference Clay Index (NDCI) = (B11 - B12) / (B11 + B12)
    ndci = np.where(valid_mask, (b11 - b12) / (b11 + b12 + eps), np.nan)

    # 5. Hydroxyl / Alteration Index (HI) = B11 / B08
    hi = np.where(valid_mask, b11 / (b8 + eps), np.nan)

    # 6. Normalized Difference Vegetation Index (NDVI) = (B08 - B04) / (B08 + B04)
    ndvi = np.where(valid_mask, (b8 - b4) / (b8 + b4 + eps), np.nan)

    # 7. Bare Ground / Exposed Placer Gravel Mask
    bare_ground = valid_mask & (ndvi <= ndvi_bare_thresh)
    if scl_data is not None:
        bare_ground &= (scl_data.astype(int) != 6)

    bare_mask = bare_ground.astype('uint8')

    # 8. Gemstone Prospectivity / Favorability Model
    print("[*] Computing Gemstone Exploration Favorability Model...")
    def zscore(arr, mask):
        vals = arr[mask]
        if len(vals) == 0:
            return np.zeros_like(arr)
        m = np.nanmean(vals)
        s = np.nanstd(vals)
        if s < eps:
            s = 1.0
        return np.where(mask, (arr - m) / s, np.nan)

    z_ior = zscore(ior, valid_mask)
    z_ndii = zscore(ndii_fe, valid_mask)
    z_cr = zscore(cr, valid_mask)
    z_ndci = zscore(ndci, valid_mask)
    z_ndvi = zscore(ndvi, valid_mask)

    # Weighted gem favorability score:
    fav_all = (0.35 * z_ior) + (0.15 * z_ndii) + (0.35 * z_cr) + (0.15 * z_ndci) - (0.5 * z_ndvi)
    fav_bare = np.where(bare_ground, fav_all, np.nan)

    # Save outputs
    out_meta = ref_meta.copy()
    out_meta.update(
        driver='GTiff',
        dtype='float32',
        count=1,
        nodata=np.nan,
        compress='lzw'
    )

    outputs = [
        ('IOR.tif', ior),
        ('NDII_Fe.tif', ndii_fe),
        ('CR.tif', cr),
        ('NDCI.tif', ndci),
        ('HI.tif', hi),
        ('NDVI.tif', ndvi),
        ('favorability_S2.tif', fav_bare),
        ('favorability_unmasked_S2.tif', fav_all),
    ]

    print(f"[*] Writing output GeoTIFFs to: {out_dir}")
    for fname, arr in outputs:
        fpath = os.path.join(out_dir, fname)
        with rasterio.open(fpath, 'w', **out_meta) as dst:
            dst.write(arr.astype('float32'), 1)
        print(f"    ✓ {fname}")

    # Write bare_mask as uint8
    mask_meta = ref_meta.copy()
    mask_meta.update(
        driver='GTiff',
        dtype='uint8',
        count=1,
        nodata=0,
        compress='lzw'
    )
    mask_path = os.path.join(out_dir, 'bare_mask.tif')
    with rasterio.open(mask_path, 'w', **mask_meta) as dst:
        dst.write(bare_mask, 1)
    print("    ✓ bare_mask.tif (1 = Bare Ground/Exposed Soil/Mines, 0 = Vegetated/Cloud/Water)")

    # Write True Color RGB (B04, B03, B02) for visual validation in QGIS
    rgb_meta = ref_meta.copy()
    rgb_meta.update(
        driver='GTiff',
        dtype='uint8',
        count=3,
        nodata=0,
        compress='lzw'
    )
    rgb_path = os.path.join(out_dir, 'RGB_TrueColor.tif')
    with rasterio.open(rgb_path, 'w', **rgb_meta) as dst:
        r = np.clip((b4 / 0.3) * 255, 0, 255).astype('uint8')
        g = np.clip((b3 / 0.3) * 255, 0, 255).astype('uint8')
        b = np.clip((b2 / 0.3) * 255, 0, 255).astype('uint8')
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)
    print("    ✓ RGB_TrueColor.tif (Visual Reference)")

    print(f"\n[✔] Processing complete! All rasters saved in: {out_dir}")


def compute_aster_indices(band_dir, out_dir):
    """
    Computes ASTER mineral indices for gemstone & alteration exploration.
    band_dir: folder containing ASTER bands (B01.tif .. B09.tif or AST_B01.tif etc.)
    out_dir: output folder
    """
    import glob
    os.makedirs(out_dir, exist_ok=True)
    bands = {}
    for i in range(1, 10):
        b = f'B{str(i).zfill(2)}'
        paths = glob.glob(os.path.join(band_dir, f'*{b}*.tif'))
        if not paths:
            raise FileNotFoundError(f"ASTER Band {b} not found in {band_dir}")
        bands[b] = paths[0]

    ref_path = bands['B04']
    with rasterio.open(ref_path) as ref:
        ref_meta = ref.meta.copy()
        ref_shape = ref.shape

    print(f"[*] ASTER Reference grid (B04 - SWIR): {ref_shape[1]}x{ref_shape[0]} px")
    aligned = {}
    for b, p in bands.items():
        aligned[b] = resample_and_read(p, ref_meta, ref_shape, Resampling.bilinear)

    b1, b2, b4 = aligned['B01'], aligned['B02'], aligned['B04']
    b5, b6, b7, b8 = aligned['B05'], aligned['B06'], aligned['B07'], aligned['B08']

    eps = 1e-6
    valid = (b1 > 0) & (b2 > 0) & (b4 > 0) & (b5 > 0) & (b6 > 0) & (b7 > 0) & (b8 > 0)

    fe1 = np.where(valid, b2 / (b1 + eps), np.nan)
    fe2 = np.where(valid, b4 / (b2 + eps), np.nan)
    cr = np.where(valid, b4 / (b6 + eps), np.nan)
    ndci = np.where(valid, (b4 - b6) / (b4 + b6 + eps), np.nan)
    mica_clay = np.where(valid, b5 / (b7 + eps), np.nan)
    cb_ratio = np.where(valid, b4 / (b8 + eps), np.nan)
    silica = np.where(valid, b4 / (b5 + eps), np.nan)

    def zscore(arr):
        vals = arr[valid]
        if len(vals) == 0:
            return np.zeros_like(arr)
        return np.where(valid, (arr - np.nanmean(vals)) / (np.nanstd(vals) + eps), np.nan)

    fav = zscore(fe1) + zscore(fe2) + zscore(cr) + zscore(ndci) + zscore(silica)

    out_meta = ref_meta.copy()
    out_meta.update(driver='GTiff', dtype='float32', count=1, nodata=np.nan, compress='lzw')

    for name, arr in [('Fe1', fe1), ('Fe2', fe2), ('CR', cr), ('NDCI', ndci),
                      ('MicaClay', mica_clay), ('CbRatio', cb_ratio), ('Silica', silica),
                      ('favorability_AST', fav)]:
        out_path = os.path.join(out_dir, f'{name}_ASTER.tif')
        with rasterio.open(out_path, 'w', **out_meta) as dst:
            dst.write(arr.astype('float32'), 1)
        print(f"    ✓ {name}_ASTER.tif")
    print(f"\n[✔] ASTER processing complete! Output saved in: {out_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Gemstone Exploration Spectral Indices Generator (Sentinel-2 & ASTER)"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Path to Sentinel-2 .SAFE folder, extracted directory, or .SAFE.zip archive (or ASTER band dir)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output_S2",
        help="Directory to save output GeoTIFF files (default: output_S2)"
    )
    parser.add_argument(
        "--sensor",
        choices=["s2", "aster"],
        default="s2",
        help="Sensor type: s2 (Sentinel-2 MSI) or aster (ASTER)"
    )
    parser.add_argument(
        "--ndvi-threshold",
        type=float,
        default=0.30,
        help="Max NDVI threshold for bare soil / exposed ground mask (default: 0.30)"
    )

    args = parser.parse_args()

    if not args.input:
        print("\n[!] No input path specified.")
        print("Usage:")
        print("  python gem_exploration_indices.py <path_to_SAFE_folder_or_zip> [--output <out_dir>]")
        print("Example:")
        print("  python gem_exploration_indices.py C:/Users/User/Downloads/S2A_MSIL2A_...SAFE --output ./ratnapura_indices\n")
        sys.exit(1)

    if args.sensor == "aster":
        compute_aster_indices(args.input, args.output)
    else:
        compute_sentinel2_indices(args.input, args.output, ndvi_bare_thresh=args.ndvi_threshold)


if __name__ == "__main__":
    main()

