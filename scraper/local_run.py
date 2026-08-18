"""Run the price check locally and write Excel + a standalone HTML dashboard.

    python -m scraper.local_run --init     # create products.xlsx template
    python -m scraper.local_run            # scrape everything in products.xlsx

Nothing is uploaded anywhere; outputs land in ./output/.
"""

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from .engine import Engine
from .inputs import load_products, write_template
from .outputs import write_excel, write_html
from .platforms import ZONE_MODULES, amazon, noon_retail
from .result import unavailable
from .zones import ZONES

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "products.xlsx"
OUTPUT_DIR = ROOT / "output"


def _as_result(value):
    """Engine hands back either a result dict or the exception that broke it."""
    if isinstance(value, BaseException):
        return unavailable("scrape error: " + str(value)[:200])
    return value


async def _run_national(engine, products, results):
    context = await engine.new_context()
    try:
        amazon_items = [
            (bc, p["platforms"]["amazon_core"])
            for bc, p in products.items()
            if "amazon_core" in p["platforms"]
        ]
        if amazon_items:
            print("  Amazon.ae + Amazon Now: " + str(len(amazon_items)) + " products")

            async def do_amazon(page, item):
                return await amazon.scrape(page, item[1])

            for item, value in await engine.run_batch(context, amazon_items, do_amazon):
                barcode = item[0]
                if isinstance(value, BaseException):
                    failed = _as_result(value)
                    results[barcode]["amazon_core"] = failed
                    results[barcode]["amazon_fast"] = dict(failed)
                else:
                    core, fast = value
                    results[barcode]["amazon_core"] = core
                    results[barcode]["amazon_fast"] = fast

        noon_items = [
            (bc, p["platforms"]["noon_retail"])
            for bc, p in products.items()
            if "noon_retail" in p["platforms"]
        ]
        if noon_items:
            print("  Noon: " + str(len(noon_items)) + " products")

            async def do_noon(page, item):
                return await noon_retail.scrape(page, item[1])

            for item, value in await engine.run_batch(context, noon_items, do_noon):
                results[item[0]]["noon_retail"] = _as_result(value)
    finally:
        await context.close()


async def _run_zoned(engine, products, results, platform_id, module):
    items = [
        (bc, p["platforms"][platform_id])
        for bc, p in products.items()
        if platform_id in p["platforms"]
    ]
    if not items:
        return

    for barcode, _ in items:
        results[barcode].setdefault(platform_id, {"zones": {}})

    for zone in ZONES:
        # One context per zone: location is established once, then every product
        # is checked inside that same darkstore session.
        context = await engine.new_context(geolocation=zone)
        try:
            print("  " + platform_id + " / " + zone["name"] + ": " + str(len(items)) + " products")
            boot = await context.new_page()
            try:
                await module.bootstrap(boot, zone)
            except Exception as exc:  # noqa: BLE001 - a failed bootstrap is reported per product
                print("    bootstrap warning: " + str(exc)[:120])
            finally:
                await boot.close()

            async def do_one(page, item, _zone=zone):
                return await module.scrape(page, item[1], _zone)

            for item, value in await engine.run_batch(context, items, do_one):
                results[item[0]][platform_id]["zones"][zone["id"]] = _as_result(value)
        finally:
            await context.close()


async def scrape_all(products: dict) -> dict:
    results = {bc: {} for bc in products}
    async with Engine() as engine:
        await _run_national(engine, products, results)
        for platform_id, module in ZONE_MODULES.items():
            await _run_zoned(engine, products, results, platform_id, module)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Local UAE price check")
    parser.add_argument("--init", action="store_true", help="write a products.xlsx template and exit")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="input spreadsheet")
    args = parser.parse_args()

    if args.init:
        write_template(args.input)
        print("Template written: " + str(args.input))
        print("Fill in one row per barcode, then run: python -m scraper.local_run")
        return 0

    products = load_products(args.input)
    if not products:
        print("No usable rows found in " + str(args.input))
        return 1

    print("Checking " + str(len(products)) + " barcode(s) across 5 platforms and " + str(len(ZONES)) + " zones...")
    started = datetime.now(timezone.utc)
    results = asyncio.run(scrape_all(products))
    checked_at = started.isoformat()

    stamp = started.strftime("%Y-%m-%d_%H%M")
    xlsx_path = OUTPUT_DIR / ("prices_" + stamp + ".xlsx")
    html_path = OUTPUT_DIR / ("dashboard_" + stamp + ".html")
    write_excel(xlsx_path, products, results, checked_at)
    write_html(html_path, products, results, checked_at)

    found = sum(
        1
        for per_platform in results.values()
        for res in per_platform.values()
        if (res.get("available") if "zones" not in res else any(
            (z or {}).get("available") for z in res["zones"].values()
        ))
    )
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print("Done in " + str(round(elapsed)) + "s. " + str(found) + " platform/product combinations returned a price.")
    print("  Excel:     " + str(xlsx_path))
    print("  Dashboard: " + str(html_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
