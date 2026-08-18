"""Shared result shape for every platform scrape."""


def ok(price: float, source: str) -> dict:
    """source records where the number came from, so provenance is auditable."""
    return {"price": float(price), "currency": "AED", "available": True, "error": None, "source": source}


def unavailable(error: str, source: str | None = None) -> dict:
    return {"price": None, "currency": "AED", "available": False, "error": error, "source": source}


def classify_failure(page_title: str, platform: str) -> str:
    """Turn a silent 'no price found' into a specific, actionable reason."""
    title = (page_title or "").strip()
    if "just a moment" in title.lower():
        return f"blocked: Cloudflare bot challenge instead of the product page ({platform})"
    if title in ("Amazon.ae", "Amazon.com"):
        return f"blocked: Amazon bot interstitial instead of the product page ({platform})"
    if not title:
        return f"page did not load ({platform})"
    return f"price not found on page - layout may have changed ({platform}); title={title[:60]!r}"
