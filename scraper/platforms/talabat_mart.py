"""Talabat Mart (talabat.com/uae/groceries) darkstore price scraper. Zone-based.

Confirmed via live recon that the grocery ordering flow (address -> nearest
branch -> catalog) exists on the web. This scraper grants browser geolocation
for the target zone and falls back to typing the zone name into Talabat's own
area-search box (seen in recon as a "Search for area, street name, landmark..."
field followed by a "Let's go" button) if the site doesn't pick up geolocation
automatically. DOM extraction selectors are a best-effort starting point and are
flagged in the plan as needing confirmation against a real item during the first
end-to-end test.
"""

import re

from ..browser import empty_result, new_page

DOM_PRICE_SELECTORS = [
    "[data-testid='item-price']",
    "[class*='price']",
]


def _product_url(ref: dict) -> str | None:
    return ref.get("url")


def scrape_price(ref: dict, zone: dict) -> dict:
    url = _product_url(ref)
    if not url:
        return empty_result("no url configured for talabat_mart")
    if not zone:
        return empty_result("talabat_mart requires a zone")

    try:
        with new_page(geolocation={"lat": zone["lat"], "lng": zone["lng"]}) as page:
            page.goto("https://www.talabat.com/uae/groceries", wait_until="networkidle", timeout=30000)
            _set_location(page, zone)

            page.goto(url, wait_until="networkidle", timeout=30000)

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
        return empty_result(f"talabat_mart scrape failed for zone '{zone['id']}': {exc}")


def _set_location(page, zone: dict) -> None:
    try:
        search_box = page.get_by_placeholder(re.compile("area, street name", re.I))
        if search_box.count() > 0:
            search_box.first.fill(zone["name"].split(" / ")[0])
            page.wait_for_timeout(1500)
            suggestion = page.locator("[role='option'], li").first
            if suggestion.count() > 0:
                suggestion.click(timeout=2000)
            go_button = page.get_by_text("Let's go", exact=False)
            if go_button.count() > 0:
                go_button.first.click(timeout=2000)
            page.wait_for_timeout(1000)
    except Exception:  # noqa: BLE001
        pass
