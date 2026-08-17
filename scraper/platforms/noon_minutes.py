"""Noon Minutes (minutes.noon.com) darkstore price scraper. Zone-based.

The site is backed by JSON endpoints under /_svc/ (confirmed via live recon:
configs, instant/session/get, catalog/*). Rather than hand-reconstruct those
request payloads blind, this scrapes by setting the browser geolocation to the
target zone, letting the site's own JS establish its darkstore session, then
either (a) intercepting the catalog response that the product page naturally
triggers, or (b) falling back to reading the rendered price from the DOM.

Exact selectors/response shape are flagged in the plan as needing confirmation
against a real SKU during the first end-to-end test.
"""

import re

from ..browser import empty_result, new_page

CATALOG_RESPONSE_PATTERN = re.compile(r"/_svc/catalog/")

DOM_PRICE_SELECTORS = [
    "[data-qa='product-price']",
    ".priceNow",
    "[class*='priceNow']",
]


def _product_url(ref: dict) -> str | None:
    if ref.get("url"):
        return ref["url"]
    if ref.get("sku"):
        return f"https://minutes.noon.com/uae-en/{ref['sku']}/p/"
    return None


def scrape_price(ref: dict, zone: dict) -> dict:
    url = _product_url(ref)
    if not url:
        return empty_result("no url/sku configured for noon_minutes")
    if not zone:
        return empty_result("noon_minutes requires a zone")

    captured_price = {}

    def on_response(response):
        if CATALOG_RESPONSE_PATTERN.search(response.url) and response.status == 200:
            try:
                data = response.json()
            except Exception:  # noqa: BLE001
                return
            price = _find_price_in_json(data, ref.get("sku"))
            if price is not None:
                captured_price["value"] = price

    try:
        with new_page(geolocation={"lat": zone["lat"], "lng": zone["lng"]}) as page:
            page.on("response", on_response)
            page.goto("https://minutes.noon.com/uae-en/", wait_until="networkidle", timeout=30000)
            _accept_location_prompt(page)

            page.goto(url, wait_until="networkidle", timeout=30000)

            if "value" in captured_price:
                return {"price": captured_price["value"], "currency": "AED", "available": True, "error": None}

            for selector in DOM_PRICE_SELECTORS:
                el = page.query_selector(selector)
                if el:
                    match = re.search(r"[\d.,]+", el.inner_text().replace(",", ""))
                    if match:
                        return {
                            "price": float(match.group()),
                            "currency": "AED",
                            "available": True,
                            "error": None,
                        }

            return empty_result(f"price not found for zone '{zone['id']}' (out of coverage or page changed)")
    except Exception as exc:  # noqa: BLE001
        return empty_result(f"noon_minutes scrape failed for zone '{zone['id']}': {exc}")


def _accept_location_prompt(page) -> None:
    for text in ["Allow", "Use my location", "Enable location"]:
        try:
            btn = page.get_by_text(text, exact=False)
            if btn.count() > 0:
                btn.first.click(timeout=2000)
                page.wait_for_timeout(1000)
                return
        except Exception:  # noqa: BLE001
            continue


def _find_price_in_json(data, sku: str | None):
    """Best-effort recursive search for a price tied to the tracked SKU."""
    if isinstance(data, dict):
        if sku and data.get("sku") == sku and "price" in data:
            try:
                return float(data["price"])
            except (TypeError, ValueError):
                pass
        for value in data.values():
            result = _find_price_in_json(value, sku)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_price_in_json(item, sku)
            if result is not None:
                return result
    return None
