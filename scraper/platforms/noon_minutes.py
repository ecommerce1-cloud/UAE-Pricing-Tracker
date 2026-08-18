"""Noon Minutes (minutes.noon.com) darkstore price scraper. Zone-based.

Confirmed via live inspection: like noon.com retail, product pages embed a
schema.org Product JSON-LD block with offers.price -- used as the primary
signal here too. The browser geolocation is set to the target zone before
navigating so the price reflects that darkstore's session/catalog. Falls back
to a DOM selector, then to intercepting the page's own /_svc/catalog response,
if JSON-LD isn't present for some reason (e.g. an out-of-coverage zone).
"""

import json
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

            price = _price_from_json_ld(page)

            if price is None:
                for selector in DOM_PRICE_SELECTORS:
                    el = page.query_selector(selector)
                    if el:
                        match = re.search(r"[\d.,]+", el.inner_text().replace(",", ""))
                        if match:
                            price = float(match.group())
                            break

            if price is None and "value" in captured_price:
                price = captured_price["value"]

            if price is not None:
                return {"price": price, "currency": "AED", "available": True, "error": None}

            title = page.title()
            print(f"[noon_minutes] zone {zone['id']}: price not found. page title: {title!r}")
            if "just a moment" in title.lower():
                return empty_result(
                    f"blocked: Cloudflare bot challenge for zone '{zone['id']}' "
                    "(datacenter IP). See SETUP.md."
                )
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
