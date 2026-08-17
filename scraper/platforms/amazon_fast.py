"""Amazon's fast-delivery ("2HR" / Amazon Now-equivalent) tier.

Not zone-based in the darkstore sense (Amazon determines eligibility server-side
from the account/session address rather than an arbitrary lat/lng), so this is
scraped once per product like amazon_core.

NOTE: the exact mechanism for confirming a product is priced/sold under the fast
tier needs validation against a real ASIN that participates in it. Current
approach: load the product page and look for a fast-delivery badge; if present,
reuse the displayed price, otherwise report unavailable rather than guessing.
"""

import re

from ..browser import empty_result, new_page
from .amazon_core import PRICE_SELECTORS, _product_url

FAST_BADGE_SELECTORS = [
    "text=/2 hour delivery/i",
    "text=/Amazon Now/i",
    "[data-testid='fast-delivery-badge']",
]


def scrape_price(ref: dict, zone: dict | None = None) -> dict:
    url = _product_url(ref)
    if not url:
        return empty_result("no url/asin configured for amazon_fast")

    try:
        with new_page() as page:
            page.goto(url, wait_until="load", timeout=30000)
            try:
                page.wait_for_selector(".a-price .a-offscreen", timeout=8000)
            except Exception:  # noqa: BLE001
                pass

            is_fast_eligible = any(page.query_selector(sel) for sel in FAST_BADGE_SELECTORS)
            if not is_fast_eligible:
                return empty_result("product not eligible for fast-delivery tier at this address")

            price_text = None
            for selector in PRICE_SELECTORS:
                el = page.query_selector(selector)
                if el:
                    price_text = el.inner_text()
                    break
            if not price_text:
                return empty_result("price element not found (page structure may have changed)")

            match = re.search(r"[\d.,]+", price_text.replace(",", ""))
            if not match:
                return empty_result(f"could not parse price from '{price_text}'")

            return {
                "price": float(match.group()),
                "currency": "AED",
                "available": True,
                "error": None,
            }
    except Exception as exc:  # noqa: BLE001
        return empty_result(f"amazon_fast scrape failed: {exc}")
