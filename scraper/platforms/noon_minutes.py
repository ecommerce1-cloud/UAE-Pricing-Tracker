"""noon Minutes (minutes.noon.com) -- darkstore model, priced per zone.

Two possible price sources, in order of preference:

1. The site's own /_svc/catalog response, intercepted as the page loads. This is
   zone-accurate because it is served for the darkstore session established for
   the context's geolocation.
2. The server-rendered JSON-LD block. Easier and faster, but it may be
   zone-invariant -- we can't be sure it reflects the selected darkstore.

Whichever is used is recorded in the result's `source` field, so if every zone
comes back identical with source="json_ld" that is a signal the JSON-LD number
is not zone-specific and only source (1) should be trusted.
"""

import re

from ..result import classify_failure, ok, unavailable
from .jsonld import price_from_json_ld

ZONE_BASED = True

CATALOG_PATTERN = re.compile(r"/_svc/catalog/")


def product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("sku"):
        return f"https://minutes.noon.com/uae-en/{ref['sku']}/p/"
    return None


async def bootstrap(page, zone: dict) -> None:
    """Establish the darkstore session for this zone once per context."""
    await page.goto("https://minutes.noon.com/uae-en/", wait_until="domcontentloaded", timeout=45000)
    for label in ("Allow", "Use my location", "Enable location"):
        try:
            btn = page.get_by_text(label, exact=False)
            if await btn.count() > 0:
                await btn.first.click(timeout=2000)
                await page.wait_for_timeout(800)
                break
        except Exception:  # noqa: BLE001
            continue


async def scrape(page, ref: dict, zone: dict) -> dict:
    url = product_url(ref)
    if not url:
        return unavailable("no noon Minutes URL/SKU configured")

    captured: dict = {}
    sku = ref.get("sku")

    async def on_response(response):
        if not CATALOG_PATTERN.search(response.url) or response.status != 200:
            return
        try:
            data = await response.json()
        except Exception:  # noqa: BLE001
            return
        found = _find_price(data, sku)
        if found is not None:
            captured["price"] = found

    page.on("response", on_response)
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)

    if "price" in captured:
        return ok(captured["price"], "catalog_api")

    price = await price_from_json_ld(page)
    if price is not None:
        return ok(price, "json_ld")

    return unavailable(classify_failure(await page.title(), f"noon_minutes/{zone['id']}"))


def _find_price(data, sku: str | None):
    """Recursive best-effort search for a price attached to the tracked SKU."""
    if isinstance(data, dict):
        if sku and data.get("sku") == sku and data.get("price") is not None:
            try:
                return float(data["price"])
            except (TypeError, ValueError):
                pass
        for value in data.values():
            hit = _find_price(value, sku)
            if hit is not None:
                return hit
    elif isinstance(data, list):
        for item in data:
            hit = _find_price(item, sku)
            if hit is not None:
                return hit
    return None
