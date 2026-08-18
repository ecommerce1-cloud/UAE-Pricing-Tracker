from . import amazon, noon_minutes, noon_retail, talabat_mart

# Display order in every output. amazon_core and amazon_fast are both produced
# by the single `amazon` module from one page load.
PLATFORMS = [
    {"id": "amazon_core", "name": "Amazon.ae", "logo": "amazon_core.svg", "zone_based": False},
    {"id": "amazon_fast", "name": "Amazon Now", "logo": "amazon_fast.svg", "zone_based": False},
    {"id": "noon_retail", "name": "Noon", "logo": "noon_retail.svg", "zone_based": False},
    {"id": "noon_minutes", "name": "Noon Minutes", "logo": "noon_minutes.svg", "zone_based": True},
    {"id": "talabat_mart", "name": "Talabat Mart", "logo": "talabat_mart.svg", "zone_based": True},
]

PLATFORM_BY_ID = {p["id"]: p for p in PLATFORMS}

ZONE_MODULES = {"noon_minutes": noon_minutes, "talabat_mart": talabat_mart}
