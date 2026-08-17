// Shared platform + zone metadata, mirrors scraper/platforms/__init__.py and scraper/zones.py
const PLATFORMS = [
  { id: "amazon_core", name: "Amazon.ae", logo: "assets/logos/amazon_core.svg", zoneBased: false },
  { id: "amazon_fast", name: "Amazon Now", logo: "assets/logos/amazon_fast.svg", zoneBased: false },
  { id: "noon_retail", name: "Noon", logo: "assets/logos/noon_retail.svg", zoneBased: false },
  { id: "noon_minutes", name: "Noon Minutes", logo: "assets/logos/noon_minutes.svg", zoneBased: true },
  { id: "talabat_mart", name: "Talabat Mart", logo: "assets/logos/talabat_mart.svg", zoneBased: true },
];

const ZONES = [
  { id: "marina_jbr", name: "Dubai Marina / JBR" },
  { id: "downtown_businessbay", name: "Downtown / Business Bay" },
  { id: "deira_burdubai", name: "Deira / Bur Dubai" },
  { id: "jumeirah_albarsha", name: "Jumeirah / Al Barsha" },
  { id: "dso_academiccity", name: "Dubai Silicon Oasis / Academic City" },
];
