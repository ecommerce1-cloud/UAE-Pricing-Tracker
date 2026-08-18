"""Noon.com retail storefront price scraper. Not zone-based (ships nationally).

Confirmed via live inspection: noon product pages embed a schema.org Product
JSON-LD block with offers.price, which is far more stable than any CSS class
name. That's used as the primary signal, with a DOM selector as fallback.
"""

import json
import re

from ..browser import empty_result, new_page

DOM_PRICE_SELECTORS = [
    "[data-qa='product-price'] .priceNow",
    ".priceNow",
    "[class*='priceNow']",
]


def _product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("sku"):
        return f"https://www.noon.com/uae-en/{ref['sku']}/p/"
    return None


def _price_from_json_ld(page) -> float | None:
    for script in page.query_selector_all("script[type='application/ld+json']"):
        try:
            data = json.loads(script.inner_text())
        except (ValueError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            offers = item.get("offers") if isinstance(item, dict) else None
            if isinstance(offers, dict) and offers.get("price"):
                try:
                    return float(offers["price"])
                except (TypeError, ValueError):
                    continue
    return None


def scrape_price(ref: dict, zone: dict | None = None) -> dict:
    url = _product_url(ref)
    if not url:
        return empty_result("no url/sku configured for noon_retail")

    try:
        with new_page() as page:
            page.goto(url, wait_until="networkidle", timeout=30000)

            price = _price_from_json_ld(page)
            if price is None:
                for selector in DOM_PRICE_SELECTORS:
                    el = page.query_selector(selector)
                    if el:
                        match = re.search(r"[\d.,]+", el.inner_text().replace(",", ""))
                        if match:
                            price = float(match.group())
                            break

            if price is None:
                title = page.title()
                print(f"[noon_retail] price not found. page title: {title!r}")
                if "just a moment" in title.lower():
                    return empty_result(
                        "blocked: Cloudflare bot challenge served instead of the product page "
                        "(datacenter IP). See SETUP.md."
                    )
                return empty_result("price not found (page structure may have changed)")

            return {"price": price, "currency": "AED", "available": True, "error": None}
    except Exception as exc:  # noqa: BLE001
        return empty_result(f"noon_retail scrape failed: {exc}")
