"""noon.com retail storefront. Nationally priced, so no zone loop.

Price comes from the server-rendered schema.org JSON-LD block, which is both
more stable than CSS class names and available at domcontentloaded -- no need to
wait for the full client-side render.
"""

from ..result import classify_failure, ok, unavailable
from .jsonld import price_from_json_ld

ZONE_BASED = False


def product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("sku"):
        return f"https://www.noon.com/uae-en/{ref['sku']}/p/"
    return None


async def scrape(page, ref: dict) -> dict:
    url = product_url(ref)
    if not url:
        return unavailable("no noon URL/SKU configured")

    await page.goto(url, wait_until="domcontentloaded", timeout=45000)

    price = await price_from_json_ld(page)
    if price is not None:
        return ok(price, "json_ld")

    return unavailable(classify_failure(await page.title(), "noon_retail"))
