"""Shared schema.org JSON-LD price extraction (both noon storefronts use it)."""

import json


async def price_from_json_ld(page) -> float | None:
    for script in await page.query_selector_all("script[type='application/ld+json']"):
        try:
            data = json.loads(await script.inner_text())
        except (ValueError, TypeError):
            continue
        for item in data if isinstance(data, list) else [data]:
            offers = item.get("offers") if isinstance(item, dict) else None
            if isinstance(offers, dict) and offers.get("price") is not None:
                try:
                    return float(offers["price"])
                except (TypeError, ValueError):
                    continue
    return None
