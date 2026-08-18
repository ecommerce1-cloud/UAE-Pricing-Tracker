"""Async scraping engine.

Replaces the original one-browser-launch-per-price-check design, which needed
~1,300 Chromium launches for 100 barcodes (~5 hours). Here a single browser is
launched once, each darkstore zone gets one context whose location is set once,
and all products are then looped inside that session with bounded concurrency.

Concurrency is deliberately modest and paced: the goal is to finish in minutes
without hammering the platforms hard enough to get the running machine's IP
throttled.
"""

import asyncio

from playwright.async_api import async_playwright

UAE_LOCALE = "en-AE"
UAE_TIMEZONE = "Asia/Dubai"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Tuned for "fast enough, still polite". Raise CONCURRENCY at your own risk --
# it multiplies request rate against the platforms from a single IP.
CONCURRENCY = 4
PER_REQUEST_DELAY = 0.4


class Engine:
    def __init__(self, concurrency: int = CONCURRENCY, delay: float = PER_REQUEST_DELAY):
        self._sem = asyncio.Semaphore(concurrency)
        self._delay = delay
        self._pw = None
        self._browser = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        return self

    async def __aexit__(self, *exc):
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def new_context(self, geolocation: dict | None = None):
        kwargs = dict(locale=UAE_LOCALE, timezone_id=UAE_TIMEZONE, user_agent=USER_AGENT)
        if geolocation:
            kwargs["geolocation"] = {"latitude": geolocation["lat"], "longitude": geolocation["lng"]}
            kwargs["permissions"] = ["geolocation"]
        return await self._browser.new_context(**kwargs)

    async def run_batch(self, context, items, handler):
        """Apply async `handler(page, item)` over `items` with bounded concurrency.

        Each task gets its own page from the shared context so a hung navigation
        can't wedge the whole batch.
        """

        async def one(item):
            async with self._sem:
                await asyncio.sleep(self._delay)
                page = await context.new_page()
                try:
                    return item, await handler(page, item)
                except Exception as exc:  # noqa: BLE001 - one bad product must not end the run
                    return item, exc
                finally:
                    await page.close()

        return await asyncio.gather(*(one(i) for i in items))
