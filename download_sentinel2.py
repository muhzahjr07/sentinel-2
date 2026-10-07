#!/usr/bin/env python3
"""
Copernicus Data Space Ecosystem (CDSE) Sentinel-2 Downloader
Tailored for Sri Lanka Gem Exploration (MGRS Tiles: 44NKM, 44NLM, 44NMM, 44NMK)

Usage:
  # 1. Search for clear scenes in Ratnapura (tile 44NKM):
  python download_sentinel2.py search --tile 44NKM --max-cloud 15

  # 2. Download a specific scene by Product ID:
  python download_sentinel2.py download --id <product_id> --user <email> --password <password>

  # 3. Or download and immediately process into gem favorability rasters:
  python download_sentinel2.py download --id <product_id> --process
"""

import os
import sys
import json
import getpass
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

CDSE_AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

LOCATION_TILES = {
    "ratnapura": "44NKM",
    "kuruwita": "44NKM",
    "eheliyagoda": "44NKM",
    "nivithigala": "44NKM",
    "pelmadulla": "44NKM",
    "balangoda": "44NLM",
    "bogawantalawa": "44NLM",
    "elahera": "44NMM",
    "bakamuna": "44NMM",
    "okkampitiya": "44NMK",
    "kataragama": "44NMK",
}


def get_access_token(username, password):
    """Authenticate with CDSE Keycloak and obtain Bearer token."""
    data = urllib.parse.urlencode({
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }).encode("utf-8")

    req = urllib.request.Request(
        CDSE_AUTH_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            return token_data["access_token"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"\n[!] Authentication failed (HTTP {e.code}): {err_msg}")
        print("    Please check your Copernicus username (email) and password.")
        sys.exit(1)


def search_scenes(tile="44NKM", max_cloud=15.0, limit=10, start_date=None, end_date=None):
    """Search for Sentinel-2 L2A scenes in Copernicus catalogue."""
    tile = tile.upper().strip()
    filter_parts = [
        "Collection/Name eq 'SENTINEL-2'",
        "contains(Name,'MSIL2A')",
        f"contains(Name,'T{tile}')",
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {float(max_cloud)})"
    ]

    if start_date:
        filter_parts.append(f"ContentDate/Start ge {start_date}T00:00:00.000Z")
    if end_date:
        filter_parts.append(f"ContentDate/Start le {end_date}T23:59:59.999Z")

    filter_expr = " and ".join(filter_parts)
    params = {
        "$filter": filter_expr,
        "$orderby": "ContentDate/Start desc",
        "$top": str(limit),
        "$expand": "Attributes"
    }

    url = CDSE_CATALOGUE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Sentinel2GemDownloader/1.0"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("value", [])
            results = []
            for it in items:
                cloud = None
                for a in it.get("Attributes", []):
                    if a.get("Name") == "cloudCover":
                        cloud = round(float(a.get("Value")), 2)
                        break
                date_str = it.get("ContentDate", {}).get("Start", "")[:10]
                results.append({
                    "id": it["Id"],
                    "name": it["Name"],
                    "date": date_str,
                    "cloud": cloud,
                    "size_mb": round(it.get("ContentLength", 0) / (1024 * 1024), 1)
                })
            return results
    except Exception as e:
        print(f"[!] Catalogue search error: {e}")
        return []


def download_product(product_id, dest_dir=".", access_token=None, username=None, password=None):
    """Download product zip file by product ID."""
    os.makedirs(dest_dir, exist_ok=True)

    # 1. Fetch product metadata to get filename
    meta_url = f"{CDSE_CATALOGUE_URL}({product_id})"
    req_meta = urllib.request.Request(meta_url, headers={"User-Agent": "Sentinel2GemDownloader/1.0"})
    with urllib.request.urlopen(req_meta) as resp:
        meta_data = json.loads(resp.read().decode("utf-8"))
        product_name = meta_data.get("Name", f"{product_id}.SAFE")

    out_zip_name = f"{product_name}.zip" if not product_name.endswith(".zip") else product_name
    out_path = os.path.join(dest_dir, out_zip_name)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 10 * 1024 * 1024:
        print(f"[*] File already exists ({round(os.path.getsize(out_path)/(1024*1024), 1)} MB): {out_path}")
        return out_path

    # 2. Authenticate if token not provided
    if not access_token:
        username = username or os.environ.get("CDSE_USER")
        password = password or os.environ.get("CDSE_PASSWORD")

        if not username:
            username = input("Enter Copernicus Data Space username (email): ").strip()
        if not password:
            password = getpass.getpass("Enter Copernicus Data Space password: ").strip()

        print("[*] Authenticating with Copernicus Data Space Ecosystem...")
        access_token = get_access_token(username, password)
        print("[✔] Authentication successful!")

    # 3. Stream download
    download_url = f"{CDSE_CATALOGUE_URL}({product_id})/$value"
    print(f"[*] Downloading: {product_name}")
    print(f"    Target path: {out_path}")

    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    req = urllib.request.Request(
        download_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Sentinel2GemDownloader/1.0"
        }
    )

    with opener.open(req) as response:
        total_length = response.headers.get('content-length')
        total_bytes = int(total_length) if total_length else None
        total_mb = f"{total_bytes / (1024*1024):.1f} MB" if total_bytes else "Unknown size"

        print(f"[*] Total file size: {total_mb}")
        downloaded = 0
        chunk_size = 1024 * 1024 * 2 # 2 MB chunks

        with open(out_path, 'wb') as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_bytes:
                    pct = downloaded / total_bytes * 100
                    mb_done = downloaded / (1024 * 1024)
                    sys.stdout.write(f"\r    Progress: {pct:5.1f}% [{mb_done:6.1f} MB / {total_mb}]")
                    sys.stdout.flush()
                else:
                    mb_done = downloaded / (1024 * 1024)
                    sys.stdout.write(f"\r    Downloaded: {mb_done:6.1f} MB")
                    sys.stdout.flush()

    print(f"\n[✔] Download complete: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Copernicus Sentinel-2 Search & Downloader")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search sub-command
    search_p = subparsers.add_parser("search", help="Search for clear Sentinel-2 scenes")
    search_p.add_argument("--tile", default=None, help="MGRS tile code (e.g., 44NKM, 44NLM, 44NMM)")
    search_p.add_argument("--location", default="ratnapura", help="Location name (e.g., ratnapura, balangoda, elahera)")
    search_p.add_argument("--max-cloud", type=float, default=15.0, help="Maximum cloud cover percentage (default: 15.0)")
    search_p.add_argument("--limit", type=int, default=8, help="Number of results (default: 8)")
    search_p.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
    search_p.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")

    # Download sub-command
    dl_p = subparsers.add_parser("download", help="Download a Sentinel-2 product")
    dl_p.add_argument("--id", required=True, help="Copernicus Product ID (UUID)")
    dl_p.add_argument("--dest", default=".", help="Directory to save downloaded zip (default: current directory)")
    dl_p.add_argument("--user", default=None, help="Copernicus username (email)")
    dl_p.add_argument("--password", default=None, help="Copernicus password")
    dl_p.add_argument("--process", action="store_true", help="Automatically run gem exploration script after download")
    dl_p.add_argument("--output-indices", default="output_S2", help="Directory for output indices GeoTIFFs")

    args = parser.parse_args()

    if args.command == "search" or args.command is None:
        tile = args.tile
        if not tile:
            loc_key = args.location.lower().strip()
            tile = LOCATION_TILES.get(loc_key, "44NKM")
            print(f"[*] Mapped location '{args.location}' -> Tile: {tile}")

        print(f"\n[*] Searching Copernicus Catalogue for Sentinel-2 L2A scenes in Tile {tile} (Cloud <= {args.max_cloud}%)...")
        scenes = search_scenes(tile, args.max_cloud, args.limit, args.start, args.end)

        if not scenes:
            print("[!] No scenes found matching criteria. Try increasing --max-cloud (e.g. --max-cloud 25).")
            return

        print(f"\n{'#':<3} | {'Date':<10} | {'Cloud %':<8} | {'Scene Name':<62} | {'Product ID'}")
        print("-" * 125)
        for idx, s in enumerate(scenes, 1):
            print(f"{idx:<3} | {s['date']:<10} | {s['cloud'] or 'N/A':<8} | {s['name'][:60]:<62} | {s['id']}")

        print("\nTo download any scene above, run:")
        print(f"  python download_sentinel2.py download --id <Product_ID> --process\n")

    elif args.command == "download":
        zip_path = download_product(args.id, dest_dir=args.dest, username=args.user, password=args.password)
        if args.process:
            print("\n[*] Launching gemstone exploration processing pipeline...")
            from gem_exploration_indices import compute_sentinel2_indices
            compute_sentinel2_indices(zip_path, args.output_indices)


if __name__ == "__main__":
    main()
