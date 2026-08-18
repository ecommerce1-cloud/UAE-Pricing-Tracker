# UAE Pricing Tracker

Barcode-level price comparison across Amazon.ae, Amazon Now (fast-delivery tier),
Noon, Noon Minutes, and Talabat Mart — all UAE, all automated inside GitHub.

- **Dashboard**: served via GitHub Pages from `/docs` — table of barcode → price
  per platform, with a CSV export button.
- **Add a barcode**: use the "+ Add barcode" page on the dashboard itself. It
  writes directly to `docs/data/tracked-products.json` via the GitHub API using a
  personal access token you generate once and paste into the page (kept only in
  your browser's local storage — never committed, never sent anywhere but
  GitHub's own API). See the in-page instructions on `add-product.html`.
- **Scraping**: `.github/workflows/scrape.yml` runs daily, scraping every tracked
  barcode across all 5 platforms (and, for the two darkstore-model platforms —
  Noon Minutes and Talabat Mart — across 5 fixed Dubai zones each) and commits
  the results back to `docs/data/latest-prices.json` and
  `docs/data/price-history.csv`. Adding a barcode via the dashboard also fires
  `on-demand-scrape.yml` so it gets priced within minutes instead of waiting for
  the next scheduled run.

## Data files

- `docs/data/tracked-products.json` — barcode → `{name, platforms: {platform_id: ref}}`.
  A `ref` is `{"asin": "..."}` / `{"sku": "..."}` / `{"url": "..."}` depending on
  the platform — see `add-product.html` for the exact fields per platform.
- `docs/data/latest-prices.json` — current snapshot, barcode → platform →
  (zone →) `{price, currency, available, error}`.
- `docs/data/price-history.csv` — append-only daily log of every check, used for
  trend analysis and full export.

## Status: prices are currently blocked

The pipeline runs end-to-end, but GitHub-hosted runners get bot-blocked by
Amazon and Noon (datacenter IPs). **See [SETUP.md](SETUP.md) for the two free
fixes** — official seller APIs, or a self-hosted runner on a UAE IP.

## Known risk

Scraping these platforms' pages/internal APIs likely isn't sanctioned by their
Terms of Service, and running from GitHub Actions' shared IP ranges raises the
chance of throttling or blocks over time. Scrapers are written to fail
gracefully per platform/zone (mark a price `unavailable`, never crash the whole
run) but expect periodic maintenance when a platform changes its frontend.

## Local development

Not required for normal use (everything runs in GitHub Actions), but to run the
scraper locally for debugging:

```
pip install -r requirements.txt
playwright install --with-deps chromium
python -m scraper.run --barcode <barcode>
```
