# UAE Pricing Tracker

Barcode-level price comparison across **Amazon.ae, Amazon Now, Noon, Noon Minutes
and Talabat Mart**, with per-zone pricing for the two darkstore platforms.

Runs on your own Windows PC. Nothing is uploaded anywhere — you get an Excel
workbook and a standalone HTML dashboard in `output/`.

## One-time setup

1. **Install Python 3.12+** — <https://www.python.org/downloads/>
   Tick **"Add python.exe to PATH"** on the first screen of the installer.
2. **Install Git for Windows** (to download this code) — <https://git-scm.com/download/win>
3. Open PowerShell and run:

```
git clone https://github.com/ecommerce1-cloud/UAE-Pricing-Tracker.git
cd UAE-Pricing-Tracker
pip install -r requirements.txt
playwright install chromium
```

## Usage

Create the input spreadsheet:

```
python -m scraper.local_run --init
```

That writes `products.xlsx` with one example row. Fill in one row per barcode:

| Column | What goes in it |
|---|---|
| Barcode | EAN/UPC, e.g. `5056141881928` |
| Product Name | Your own label, shown on the dashboard |
| Amazon | Product URL **or** just the ASIN (`B092BTLHZX`) |
| Noon | Product URL or SKU |
| Noon Minutes | Product URL or SKU |
| Talabat Mart | Product URL |

Leave a platform blank if the product isn't sold there — its column shows `—`.
The Amazon column feeds both the Amazon.ae and Amazon Now columns from a single
page load.

Then run it:

```
python -m scraper.local_run
```

Outputs land in `output/`:

- **`prices_<date>.xlsx`** — *Summary* sheet is the grid (barcode on the left,
  platforms across, darkstore columns as `min-max`); *By Zone* sheet has every
  zone, every note and the price source.
- **`dashboard_<date>.html`** — double-click to open. Logos under each platform
  name, click any "5 zones ▾" to expand the per-zone breakdown, hover a `⚠` or
  `—` to see why a cell is empty, and there's an Export CSV button.

A [layout preview with sample data](https://ecommerce1-cloud.github.io/UAE-Pricing-Tracker/demo.html)
is available if you want to see the dashboard before running anything.

## Zones

The two darkstore platforms are checked at five fixed Dubai coordinates: Dubai
Marina/JBR, Downtown/Business Bay, Deira/Bur Dubai, Jumeirah/Al Barsha, and
Dubai Silicon Oasis/Academic City. See `scraper/zones.py` to change them.

## Things worth knowing

**Price provenance.** Every price records where it came from — `catalog_api`
(zone-accurate), `json_ld` (server-rendered, may not vary by zone) or `dom`.
If all five Noon Minutes zones return the same number with source `json_ld`,
that price is probably *not* zone-specific and only `catalog_api` rows should be
trusted for zone comparisons.

**Request volume.** 100 barcodes is roughly 1,200 page loads per run. Concurrency
is capped at 4 with a delay between requests (`scraper/engine.py`) to keep the
rate down — pushing it higher risks getting your IP throttled by these
platforms, which would break the tool and affect normal browsing from the same
connection. Prefer running once a day, not on a tight loop.

**Why it isn't automated in the cloud.** GitHub-hosted runners get bot-blocked:
Amazon serves an interstitial and Noon serves a Cloudflare challenge to
datacenter IPs. Verified from real run logs. See [SETUP.md](SETUP.md) for the
alternatives, including the official seller APIs, which is the right answer if
you outgrow this.

**Maintenance.** These are scrapers against pages that change. Expect occasional
breakage; the `Note` column tells you whether a failure was a block, a layout
change or an untracked product.
