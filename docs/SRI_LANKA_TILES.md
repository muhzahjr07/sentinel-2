# Sri Lanka Gemstone Mining Districts & Sentinel-2 MGRS Tiles

This reference documents the primary gemstone exploration districts across Sri Lanka, their geographic coordinates, geological formations, and corresponding Sentinel-2 MGRS (Military Grid Reference System) tile identifiers.

---

## 1. MGRS Tile Index Table

| Locality | District / Province | Geological Complex | Latitude (°N) | Longitude (°E) | Sentinel-2 MGRS Tile | Primary Gem Varieties |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ratnapura** | Ratnapura / Sabaragamuwa | Highland Complex | 6.6828 | 80.4036 | `44NKM` | Blue Sapphire, Ruby, Cat's Eye, Spinel |
| **Ambewila** | Ratnapura / Sabaragamuwa | Highland Complex | 6.5263 | 80.7259 | `44NKM` | Blue Sapphire, Star Sapphire, Zircon |
| **Kuruwita** | Ratnapura / Sabaragamuwa | Highland Complex | 6.7725 | 80.3664 | `44NKM` | Yellow Sapphire, Tourmaline, Chrysoberyl |
| **Eheliyagoda** | Ratnapura / Sabaragamuwa | Highland Complex | 6.8486 | 80.2608 | `44NKM` | Garnet, Sapphire, Spinel |
| **Pelmadulla** | Ratnapura / Sabaragamuwa | Highland Complex | 6.6217 | 80.5486 | `44NKM` | High-grade Blue Sapphire, Padparadscha |
| **Nivithigala** | Ratnapura / Sabaragamuwa | Highland Complex | 6.6011 | 80.4503 | `44NKM` | Alluvial Sapphire, Chrysoberyl Cat's Eye |
| **Balangoda** | Ratnapura / Sabaragamuwa | Highland Complex | 6.6500 | 80.7000 | `44NLM` | Geuda Corundum, Zircon, Spinel |
| **Bogawantalawa** | Nuwara Eliya / Central | Highland Complex | 6.8000 | 80.6667 | `44NLM` | "Valley of Gems", Blue Sapphire, Ruby |
| **Elahera** | Matale / Central | Highland Complex | 7.7472 | 80.8406 | `44NMM` | Alexandrite, Cat's Eye, Tourmaline |
| **Bakamuna** | Polonnaruwa / North Central | Highland Complex | 7.7833 | 80.9000 | `44NMM` | Chrysoberyl, Corundum, Garnet |
| **Okkampitiya** | Monaragala / Uva | Vijayan / Highland Boundary | 6.8833 | 81.3167 | `44NMK` | Blue Sapphire, Spinel, Zircon |
| **Kataragama** | Monaragala / Uva | Vijayan Complex | 6.4167 | 81.3333 | `44NMK` | Star Corundum, Chert, Quartz |
| **Algama** | Kegalle / Sabaragamuwa | Highland Complex | 7.1334 | 80.1603 | `44NKM` | Alluvial Gravel Placer Formations |

---

## 2. Using Locality Presets in CLI

The `download_sentinel2.py` downloader incorporates an internal mapping dictionary. You can pass the locality name directly:

```bash
# Query scenes over Elahera using the location alias
python download_sentinel2.py search --location elahera --max-cloud 15

# Query scenes over Balangoda
python download_sentinel2.py search --location balangoda --max-cloud 10

# Or query directly via MGRS tile code
python download_sentinel2.py search --tile 44NLM --max-cloud 10
```
