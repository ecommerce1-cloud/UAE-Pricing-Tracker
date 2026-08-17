from . import amazon_core, amazon_fast, noon_retail, noon_minutes, talabat_mart

# id -> (display name, logo filename, module, zone_based)
PLATFORMS = {
    "amazon_core": {
        "name": "Amazon.ae",
        "logo": "amazon_core.svg",
        "module": amazon_core,
        "zone_based": False,
    },
    "amazon_fast": {
        "name": "Amazon Now",
        "logo": "amazon_fast.svg",
        "module": amazon_fast,
        "zone_based": False,
    },
    "noon_retail": {
        "name": "Noon",
        "logo": "noon_retail.svg",
        "module": noon_retail,
        "zone_based": False,
    },
    "noon_minutes": {
        "name": "Noon Minutes",
        "logo": "noon_minutes.svg",
        "module": noon_minutes,
        "zone_based": True,
    },
    "talabat_mart": {
        "name": "Talabat Mart",
        "logo": "talabat_mart.svg",
        "module": talabat_mart,
        "zone_based": True,
    },
}

PLATFORM_ORDER = list(PLATFORMS.keys())
