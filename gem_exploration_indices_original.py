
import os
import glob
import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling


def align_to_ref(ref_path, src_path, out_path):
    """Reproject & resample src to match reference (ref_path) using nearest."""
    with rasterio.open(ref_path) as ref:
        ref_meta = ref.meta.copy()
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_shape = ref.shape
    with rasterio.open(src_path) as src:
        data = src.read(1)
        src_crs = src.crs
        src_transform = src.transform
    dst_data = np.empty(ref_shape, dtype=src.dtypes[0])
    reproject(
        source=data,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.nearest
    )
    out_meta = ref_meta.copy()
    out_meta.update(dtype=src.dtypes[0], count=1)
    with rasterio.open(out_path, 'w', **out_meta) as dst:
        dst.write(dst_data, 1)


def compute_sentinel2_indices(band_dir, out_dir):
    """
    band_dir: folder containing B02.tif, B03.tif, B04.tif, B08.tif, B11.tif, B12.tif (all same CRS/res already, or B02 as ref)
    out_dir: folder to write index rasters
    """
    os.makedirs(out_dir, exist_ok=True)
    bands = {}
    for b in ['B02','B03','B04','B08','B11','B12']:
        paths = glob.glob(os.path.join(band_dir, f'{b}*.tif'))
        if not paths:
            raise FileNotFoundError(f"Band {b} not found in {band_dir}")
        bands[b] = paths[0]
    # Use B04 as reference (10m)
    ref = bands['B04']
    aligned = {}
    for b, p in bands.items():
        ap = os.path.join(out_dir, f'{b}_aligned.tif')
        align_to_ref(ref, p, ap)
        aligned[b] = ap
    eps = 1e-6
    def read_band(path):
        with rasterio.open(path) as src:
            return src.read(1).astype('float32')
    b2 = read_band(aligned['B02'])
    b3 = read_band(aligned['B03'])
    b4 = read_band(aligned['B04'])
    b8 = read_band(aligned['B08'])
    b11 = read_band(aligned['B11'])
    b12 = read_band(aligned['B12'])
    # Indices
    ior = b4 / (b2 + eps)
    ndii_fe = (b4 - b2) / (b4 + b2 + eps)
    cr = b11 / (b12 + eps)
    ndci = (b11 - b12) / (b11 + b12 + eps)
    hi = b11 / (b8 + eps)
    ndvi = (b8 - b4) / (b8 + b4 + eps)
    # Write
    with rasterio.open(ref) as src:
        meta = src.meta.copy()
    meta.update(dtype='float32', count=1)
    for name, arr in [('IOR', ior), ('NDII_Fe', ndii_fe), ('CR', cr), ('NDCI', ndci), ('HI', hi), ('NDVI', ndvi)]:
        out_path = os.path.join(out_dir, f'{name}.tif')
        with rasterio.open(out_path, 'w', **meta) as dst:
            dst.write(arr, 1)
    # Bare-ground mask (NDVI <= 0.3)
    mask = (ndvi <= 0.3).astype('uint8')
    with rasterio.open(os.path.join(out_dir, 'bare_mask.tif'), 'w', **meta) as dst:
        dst.write(mask, 1)
    # Optional favorability (simple sum of standardized indices)
    def zscore(x):
        return (x - np.nanmean(x)) / (np.nanstd(x) + eps)
    fav = zscore(ior) + zscore(ndii_fe) + zscore(cr) + zscore(ndci) - zscore(ndvi)
    with rasterio.open(os.path.join(out_dir, 'favorability_S2.tif'), 'w', **meta) as dst:
        dst.write(fav, 1)

if __name__ == '__main__':
    # Example usage:
    # compute_sentinel2_indices('path/to/S2_bands', 'path/to/output_S2')
    pass

def compute_aster_indices(band_dir, out_dir):
    """
    band_dir: folder containing ASTER bands named like:
      B01.tif .. B09.tif (or AST_B01.tif etc.)
    out_dir: output folder
    Bands needed: B01–B09 (use B04 as ref for SWIR alignment if needed)
    """
    os.makedirs(out_dir, exist_ok=True)
    bands = {}
    for b in [f'B{str(i).zfill(2)}' for i in range(1,10)]:
        paths = glob.glob(os.path.join(band_dir, f'*{b}*.tif'))
        if not paths:
            raise FileNotFoundError(f"Band {b} not found in {band_dir}")
        bands[b] = paths[0]
    # Use B04 (SWIR, 30m) as reference
    ref = bands['B04']
    aligned = {}
    for b, p in bands.items():
        ap = os.path.join(out_dir, f'{b}_aligned.tif')
        align_to_ref(ref, p, ap)
        aligned[b] = ap
    eps = 1e-6
    def read_band(path):
        with rasterio.open(path) as src:
            return src.read(1).astype('float32')
    b1 = read_band(aligned['B01'])
    b2 = read_band(aligned['B02'])
    b4 = read_band(aligned['B04'])
    b5 = read_band(aligned['B05'])
    b6 = read_band(aligned['B06'])
    b7 = read_band(aligned['B07'])
    b8 = read_band(aligned['B08'])
    # Indices
    fe1 = b2 / (b1 + eps)
    fe2 = b4 / (b2 + eps)
    cr = b4 / (b6 + eps)
    ndci = (b4 - b6) / (b4 + b6 + eps)
    mica_clay = b5 / (b7 + eps)
    cb_ratio = b4 / (b8 + eps)
    silica = b4 / (b5 + eps)
    # Write
    with rasterio.open(ref) as src:
        meta = src.meta.copy()
    meta.update(dtype='float32', count=1)
    for name, arr in [('Fe1', fe1), ('Fe2', fe2), ('CR', cr), ('NDCI', ndci),
                      ('MicaClay', mica_clay), ('CbRatio', cb_ratio), ('Silica', silica)]:
        out_path = os.path.join(out_dir, f'{name}_ASTER.tif')
        with rasterio.open(out_path, 'w', **meta) as dst:
            dst.write(arr, 1)
    # Optional favorability for gem-alluvial
    def zscore(x):
        return (x - np.nanmean(x)) / (np.nanstd(x) + eps)
    fav = zscore(fe1) + zscore(fe2) + zscore(cr) + zscore(ndci) + zscore(silica)
    with rasterio.open(os.path.join(out_dir, 'favorability_AST.tif'), 'w', **meta) as dst:
        dst.write(fav, 1)

if __name__ == '__main__':
    # compute_aster_indices('path/to/ASTER_bands', 'path/to/output_AST')
    pass
