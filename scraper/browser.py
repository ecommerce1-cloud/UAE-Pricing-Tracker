"""Shared Playwright helper for all platform scrapers."""

from contextlib import contextmanager

from playwright.sync_api import sync_playwright

UAE_LOCALE = "en-AE"
UAE_TIMEZONE = "Asia/Dubai"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@contextmanager
def new_page(geolocation: dict | None = None):
    """Yields a fresh Playwright page configured for UAE browsing.

    geolocation: optional {"lat": float, "lng": float} to simulate a Dubai zone.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_kwargs = dict(
            locale=UAE_LOCALE,
            timezone_id=UAE_TIMEZONE,
            user_agent=USER_AGENT,
        )
        if geolocation:
            context_kwargs["geolocation"] = {"latitude": geolocation["lat"], "longitude": geolocation["lng"]}
            context_kwargs["permissions"] = ["geolocation"]
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def empty_result(error: str | None = None) -> dict:
    return {"price": None, "currency": "AED", "available": False, "error": error}
