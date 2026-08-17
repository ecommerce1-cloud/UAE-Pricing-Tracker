"""Fixed Dubai zones used for darkstore-model platforms (Noon Minutes, Talabat Mart).

Nationally-priced platforms (Amazon core/fast, Noon Retail) ignore zones and are
scraped once per product.
"""

ZONES = [
    {"id": "marina_jbr", "name": "Dubai Marina / JBR", "lat": 25.0805, "lng": 55.1403},
    {"id": "downtown_businessbay", "name": "Downtown / Business Bay", "lat": 25.1972, "lng": 55.2744},
    {"id": "deira_burdubai", "name": "Deira / Bur Dubai", "lat": 25.2582, "lng": 55.3047},
    {"id": "jumeirah_albarsha", "name": "Jumeirah / Al Barsha", "lat": 25.1121, "lng": 55.1892},
    {"id": "dso_academiccity", "name": "Dubai Silicon Oasis / Academic City", "lat": 25.1216, "lng": 55.3773},
]

ZONE_BY_ID = {z["id"]: z for z in ZONES}
