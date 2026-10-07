# Geological & Remote Sensing Methodology

This document outlines the geological background, spectral band physics, and algorithmic formulations implemented in the **Sentinel-2 & Multi-Sensor Gemstone Exploration Toolkit**.

---

## 1. Geological Setting: Sri Lanka Gemstone Belts

Sri Lanka is world-renowned for its exceptional gem deposits, yielding high-grade corundum (blue sapphire, star sapphire, ruby, yellow sapphire, padparadscha), chrysoberyl (cat's eye, alexandrite), spinel, zircon, tourmaline, garnet, and beryl.

### 1.1 Lithotectonic Units
The island's crystalline basement is divided into three primary Precambrian metamorphic complexes:
1. **Highland Complex (HC)**: High-grade granulite-facies metamorphic belt traversing the central highlands (Ratnapura, Balangoda, Elahera). This belt hosts the primary source lithologies (pelitic gneisses, marble skarns, corundum-bearing pegmatites, and calc-silicate granulites).
2. **Vijayan Complex (VC)**: Amphibolite-facies granitoid gneisses and migmatites east of the Highland Complex (Okkampitiya, Kataragama).
3. **Wanni Complex (WC)**: Amphibolite-to-granulite facies rocks west and northwest of the Highland Complex.

### 1.2 "Illam" Alluvial Placer Deposits
Over 95% of gem mining in Sri Lanka targets **secondary alluvial placers** locally referred to as **Illam**. 
- **Illam Formation**: Millions of years of tropical weathering (lateritization and saprolitization) have decomposed metamorphic host rocks. Dense, resistant minerals (corundum hardness 9, chrysoberyl hardness 8.5) are eroded and transported via fluvial networks, accumulating in paleochannels, alluvial gravel layers, river bends, and valley basins beneath muddy overburdens.
- **Surface Signatures**: Exposed illam gravels, artisanal mining pits, tailings, and saprolitic soil profiles exhibit distinct mineralogical anomalies—notably elevated **ferric iron oxides (limonite, goethite, hematite)** and **weathered aluminosilicate clays (kaolinite, illite)**.

---

## 2. Spectral Mineral Indices (Sentinel-2 MSI)

The Multi-Spectral Instrument (MSI) on Copernicus Sentinel-2 offers 13 spectral bands from visible to shortwave infrared (SWIR).

| Band | Name | Central Wavelength ($\mu m$) | Spatial Resolution | Key Exploration Role |
| :--- | :--- | :--- | :--- | :--- |
| **B02** | Blue | 0.490 | 10 m | Ferric iron ($Fe^{3+}$) absorption minimum |
| **B03** | Green | 0.560 | 10 m | Visible reflectance & True Color generation |
| **B04** | Red | 0.665 | 10 m | Ferric iron reflectance peak & NDVI red channel |
| **B08** | NIR | 0.842 | 10 m | Chlorophyll reflectance peak (vegetation screening) |
| **B11** | SWIR-1 | 1.610 | 20 m (Resampled to 10 m) | Broad clay & hydroxyl reflectance plateau |
| **B12** | SWIR-2 | 2.190 | 20 m (Resampled to 10 m) | $Al-OH$ molecular vibrational absorption trough |
| **SCL** | Scene Classification | Categorical | 20 m | Automated cloud, cloud shadow & water masking |

---

### 2.1 Iron Oxide Ratio (IOR) & NDII_Fe
Ferric minerals ($Fe^{3+}$ in hematite $\mathrm{Fe_2O_3}$ and goethite $\mathrm{FeO(OH)}$) show intense electronic transition absorptions in the ultraviolet and blue spectrum ($0.40 - 0.50\,\mu\mathrm{m}$) with elevated reflectance in the red ($0.60 - 0.70\,\mu\mathrm{m}$).

$$\mathrm{IOR} = \frac{\mathrm{Band\ 4\ (Red)}}{\mathrm{Band\ 2\ (Blue)} + \varepsilon}$$

$$\mathrm{NDII_{Fe}} = \frac{\mathrm{Band\ 4} - \mathrm{Band\ 2}}{\mathrm{Band\ 4} + \mathrm{Band\ 2} + \varepsilon}$$

**Exploration Utility:** Identifies iron-stained gravel terraces, lateritic soils, and saprolite weathering horizons that frequently encapsulate gem-bearing illam beds.

---

### 2.2 Clay Mineral Ratio (CR) & NDCI
Aluminous clay minerals (kaolinite $\mathrm{Al_2Si_2O_5(OH)_4}$, illite, and smectite) exhibit sharp overtone vibrational absorptions near $2.20\,\mu\mathrm{m}$ due to $Al-OH$ bond stretching.

$$\mathrm{CR} = \frac{\mathrm{Band\ 11\ (SWIR\text{-}1)}}{\mathrm{Band\ 12\ (SWIR\text{-}2)} + \varepsilon}$$

$$\mathrm{NDCI} = \frac{\mathrm{Band\ 11} - \mathrm{Band\ 12}}{\mathrm{Band\ 11} + \mathrm{Band\ 12} + \varepsilon}$$

**Exploration Utility:** High CR/NDCI anomalies map intense feldspar hydrolysis and clay alteration pockets, pinpointing decomposed pegmatite contacts and silt-trap alluvial basins where heavy minerals settle.

---

### 2.3 Hydroxyl / Alteration Index (HI)
Measures the general presence of hydrous phyllosilicates and hydroxylated alterational phases:

$$\mathrm{HI} = \frac{\mathrm{Band\ 11\ (SWIR\text{-}1)}}{\mathrm{Band\ 8\ (NIR)} + \varepsilon}$$

---

### 2.4 Vegetation Screening & Bare Ground Masking
Sri Lanka's tropical climate generates dense agricultural and rainforest cover. Dense canopy obfuscates mineral spectral signatures. To isolate true soil and placer signatures:

$$\mathrm{NDVI} = \frac{\mathrm{Band\ 8\ (NIR)} - \mathrm{Band\ 4\ (Red)}}{\mathrm{Band\ 8\ (NIR)} + \mathrm{Band\ 4\ (Red)} + \varepsilon}$$

**Placer Bare Ground Filter:**
$$\mathrm{Mask_{bare}} = (\mathrm{NDVI} \le 0.30) \land (\mathrm{SCL} \ne \mathrm{Water}) \land (\mathrm{SCL} \notin \mathrm{Clouds/Shadows})$$

This mask isolates bare riverbeds, exposed agricultural fields during tilling, cleared stream corridors, and artisanal open-cast gem pits.

---

## 3. Multi-Criteria Gemstone Favorability Model

To integrate these complementary spectral indicators into an actionable targeting layer, the toolkit normalizes each index into standard deviations ($Z$-scores) over valid terrestrial pixels:

$$Z(X) = \frac{X - \mu_X}{\sigma_X}$$

The integrated Gemstone Favorability Score ($Z_{fav}$) is calculated as:

$$Z_{fav} = 0.35 \cdot Z(\mathrm{IOR}) + 0.15 \cdot Z(\mathrm{NDII_{Fe}}) + 0.35 \cdot Z(\mathrm{CR}) + 0.15 \cdot Z(\mathrm{NDCI}) - 0.50 \cdot Z(\mathrm{NDVI})$$

- **Masked Favorability (`favorability_S2.tif`)**: Retains scores exclusively on bare ground and low-vegetation cells.
- **Unmasked Favorability (`favorability_unmasked_S2.tif`)**: Evaluates regional trends across partial canopy.

---

## 4. Copernicus Baseline >= 04.00 BOA Offset Correction

Products processed by ESA after January 25, 2022 (Processing Baseline $\ge$ 04.00) include a positive radiometric offset of +1000 Digital Numbers (DN) to prevent negative reflectance clipping over dark surfaces:

$$\rho_{BOA} = \frac{\mathrm{DN} - 1000}{10000}$$

The pipeline automatically inspects lower percentiles of raw bands. If the +1000 DN bias is detected, it subtracts the offset prior to calculating band ratios, ensuring consistent reflectance values.

---

## 5. ASTER Mineral Alteration Processing

For regional exploration, the toolkit provides an ASTER (Advanced Spaceborne Thermal Emission and Reflection Radiometer) processor:

- **Iron Index 1 (Fe1)**: $B02 / B01$
- **Iron Index 2 (Fe2)**: $B04 / B02$
- **Clay / Al-OH Ratio (CR)**: $B04 / B06$
- **Mica / Clay Ratio**: $B05 / B07$
- **Carbonate Ratio (CbRatio)**: $B04 / B08$
- **Silica Index**: $B04 / B05$
- **ASTER Favorability**: $Z(\mathrm{Fe1}) + Z(\mathrm{Fe2}) + Z(\mathrm{CR}) + Z(\mathrm{NDCI}) + Z(\mathrm{Silica})$
