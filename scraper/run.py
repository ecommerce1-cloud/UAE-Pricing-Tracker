"""Orchestrator: reads tracked-products.json, scrapes every platform (and zone,
where applicable) for every tracked barcode, writes latest-prices.json and
appends today's rows to price-history.csv.

Usage:
    python -m scraper.run                   # scrape every tracked barcode
    python -m scraper.run --barcode 6291...  # scrape a single barcode (on-demand)
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .platforms import PLATFORMS
from .zones import ZONES

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
TRACKED_PATH = DATA_DIR / "tracked-products.json"
LATEST_PATH = DATA_DIR / "latest-prices.json"
HISTORY_PATH = DATA_DIR / "price-history.csv"


def load_tracked() -> dict:
    if not TRACKED_PATH.exists():
        return {}
    return json.loads(TRACKED_PATH.read_text(encoding="utf-8"))


def load_latest() -> dict:
    if not LATEST_PATH.exists():
        return {}
    return json.loads(LATEST_PATH.read_text(encoding="utf-8"))


def scrape_product(barcode: str, product: dict) -> dict:
    result = {}
    refs = product.get("platforms", {})

    for platform_id, platform in PLATFORMS.items():
        ref = refs.get(platform_id)
        if not ref:
            continue

        if platform["zone_based"]:
            zone_results = {}
            for zone in ZONES:
                zone_results[zone["id"]] = platform["module"].scrape_price(ref, zone)
            result[platform_id] = {"zones": zone_results}
        else:
            result[platform_id] = platform["module"].scrape_price(ref, None)

    return result


def append_history(barcode: str, product_name: str, results: dict, checked_at: str) -> None:
    is_new = not HISTORY_PATH.exists()
    with HISTORY_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["checked_at", "barcode", "product_name", "platform", "zone", "price", "currency", "available"])
        for platform_id, data in results.items():
            if "zones" in data:
                for zone_id, price_data in data["zones"].items():
                    writer.writerow([
                        checked_at, barcode, product_name, platform_id, zone_id,
                        price_data["price"], price_data["currency"], price_data["available"],
                    ])
            else:
                writer.writerow([
                    checked_at, barcode, product_name, platform_id, "",
                    data["price"], data["currency"], data["available"],
                ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--barcode", help="Scrape only this barcode (on-demand run)")
    args = parser.parse_args()

    tracked = load_tracked()
    if not tracked:
        print("No tracked products found in docs/data/tracked-products.json", file=sys.stderr)
        return 0

    targets = {args.barcode: tracked[args.barcode]} if args.barcode else tracked
    if args.barcode and args.barcode not in tracked:
        print(f"Barcode {args.barcode} not found in tracked-products.json", file=sys.stderr)
        return 1

    latest = load_latest()
    checked_at = datetime.now(timezone.utc).isoformat()

    for barcode, product in targets.items():
        print(f"Scraping {barcode} ({product.get('name', 'unnamed')})...")
        results = scrape_product(barcode, product)
        latest[barcode] = {
            "name": product.get("name"),
            "checked_at": checked_at,
            "platforms": results,
        }
        append_history(barcode, product.get("name", ""), results, checked_at)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print(f"Wrote {LATEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
