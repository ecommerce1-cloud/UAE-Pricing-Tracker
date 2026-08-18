"""Amazon.ae -- core storefront and the fast-delivery ("Amazon Now") tier.

Both tiers come from a single page load: for a given ASIN the fast tier carries
the same offer price, so loading the page twice would double the request volume
for no extra information. The fast column instead reports whether the product is
fast-delivery eligible at all.
"""

import re

from ..result import classify_failure, ok, unavailable

PRICE_SELECTORS = [
    "#corePrice_feature_div span.a-price span.a-offscreen",
    "#corePriceDisplay_desktop_feature_div span.a-price span.a-offscreen",
    "span.a-price span.a-offscreen",
    "#priceblock_ourprice",
]

FAST_BADGE_SELECTORS = [
    "text=/2 hour delivery/i",
    "text=/Amazon Now/i",
    "[data-testid='fast-delivery-badge']",
]

ZONE_BASED = False


def product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("asin"):
        return f"https://www.amazon.ae/dp/{ref['asin']}"
    return None


async def scrape(page, ref: dict) -> tuple[dict, dict]:
    """Returns (amazon_core_result, amazon_fast_result)."""
    url = product_url(ref)
    if not url:
        miss = unavailable("no Amazon URL/ASIN configured")
        return miss, dict(miss)

    await page.goto(url, wait_until="load", timeout=45000)
    try:
        await page.wait_for_selector(".a-price .a-offscreen", timeout=8000)
    except Exception:  # noqa: BLE001 - fall through to the selector loop
        pass

    price = None
    for selector in PRICE_SELECTORS:
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            match = re.search(r"[\d.,]+", text.replace(",", ""))
            if match:
                price = float(match.group())
                break

    if price is None:
        reason = classify_failure(await page.title(), "amazon")
        return unavailable(reason), unavailable(reason)

    core = ok(price, "dom")

    fast_eligible = False
    for selector in FAST_BADGE_SELECTORS:
        if await page.query_selector(selector):
            fast_eligible = True
            break

    fast = ok(price, "dom") if fast_eligible else unavailable("not fast-delivery eligible")
    return core, fast
