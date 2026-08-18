"""Talabat Mart -- darkstore model, priced per zone.

The zone is established once per context by granting geolocation and, if the
site doesn't pick that up, typing the area into Talabat's own area-search box.
"""

import re

from ..result import classify_failure, ok, unavailable

ZONE_BASED = True

PRICE_SELECTORS = [
    "[data-testid='item-price']",
    "[class*='price']",
]


def product_url(ref: dict) -> str | None:
    return ref.get("url")


async def bootstrap(page, zone: dict) -> None:
    await page.goto("https://www.talabat.com/uae/groceries", wait_until="domcontentloaded", timeout=45000)
    try:
        box = page.get_by_placeholder(re.compile("area, street name", re.I))
        if await box.count() > 0:
            await box.first.fill(zone["name"].split(" / ")[0])
            await page.wait_for_timeout(1500)
            suggestion = page.locator("[role='option'], li").first
            if await suggestion.count() > 0:
                await suggestion.click(timeout=2000)
            go = page.get_by_text("Let's go", exact=False)
            if await go.count() > 0:
                await go.first.click(timeout=2000)
            await page.wait_for_timeout(800)
    except Exception:  # noqa: BLE001 - geolocation alone may already be enough
        pass


async def scrape(page, ref: dict, zone: dict) -> dict:
    url = product_url(ref)
    if not url:
        return unavailable("no Talabat Mart URL configured")

    await page.goto(url, wait_until="domcontentloaded", timeout=45000)

    for selector in PRICE_SELECTORS:
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            match = re.search(r"[\d.,]+", text.replace(",", ""))
            if match:
                return ok(float(match.group()), "dom")

    return unavailable(classify_failure(await page.title(), f"talabat_mart/{zone['id']}"))
