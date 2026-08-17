"""Amazon.ae core storefront price scraper. Not zone-based (national pricing)."""

import re

from ..browser import empty_result, new_page

PRICE_SELECTORS = [
    "#corePrice_feature_div span.a-price span.a-offscreen",
    "#corePriceDisplay_desktop_feature_div span.a-price span.a-offscreen",
    "span.a-price span.a-offscreen",
    "#priceblock_ourprice",
]


def _product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("asin"):
        return f"https://www.amazon.ae/dp/{ref['asin']}"
    return None


def scrape_price(ref: dict, zone: dict | None = None) -> dict:
    url = _product_url(ref)
    if not url:
        return empty_result("no url/asin configured for amazon_core")

    try:
        with new_page() as page:
            page.goto(url, wait_until="load", timeout=30000)
            try:
                page.wait_for_selector(".a-price .a-offscreen", timeout=8000)
            except Exception:  # noqa: BLE001 - fall through to selector loop below
                pass

            price_text = None
            for selector in PRICE_SELECTORS:
                el = page.query_selector(selector)
                if el:
                    price_text = el.inner_text()
                    break

            if not price_text:
                print(f"[amazon_core] price not found. page title: {page.title()!r}")
                return empty_result("price element not found (page structure may have changed, or bot-blocked)")

            match = re.search(r"[\d.,]+", price_text.replace(",", ""))
            if not match:
                return empty_result(f"could not parse price from '{price_text}'")

            return {
                "price": float(match.group()),
                "currency": "AED",
                "available": True,
                "error": None,
            }
    except Exception as exc:  # noqa: BLE001 - scrapers must fail gracefully, never crash the run
        return empty_result(f"amazon_core scrape failed: {exc}")
