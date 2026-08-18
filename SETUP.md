# Why this runs locally, and what to do if you outgrow it

The tool runs on your own PC (see [README.md](README.md)). This file explains why
the cloud option was ruled out, and what the upgrade paths are.

## The problem with running it in the cloud

The scrapers work, but GitHub-hosted runners can't reach the product pages.
Confirmed from real workflow logs:

| Platform | What the runner actually received |
|---|---|
| Amazon.ae | Page title `Amazon.ae`, body = *"Click the button below to continue shopping"* — Amazon's bot interstitial |
| Noon / Noon Minutes | Page title `Just a moment...` — Cloudflare bot challenge |

Both are **IP-reputation blocks**, not selector bugs. GitHub Actions runs from
shared datacenter IP ranges outside the UAE, which these platforms treat as bot
traffic. No amount of selector tuning fixes this, and this repo deliberately
does **not** try to defeat those challenges.

There are two free ways to fix it. They can be combined.

---

## Path A — Use the official seller APIs (best, free, permanent)

If Hotpack sells on these platforms, you can get **authoritative** prices from
their APIs instead of scraping. No blocking, no breakage when a page redesigns,
no ToS grey area.

### Amazon.ae → SP-API (Selling Partner API)

Free with a Seller Central account. The **Product Pricing API** returns the live
selling price and competing offers for an ASIN:

- `getItemOffers` / `getCompetitiveSummary` — current offers + featured (buy box) price
- UAE marketplace ID: `A2VIGQ35RCS4UG`

Setup: Seller Central → Apps & Services → Develop Apps → create app → get
LWA `client_id`, `client_secret`, and a `refresh_token`.

> Note: the old **Product Advertising API (PA-API) was shut down 15 May 2026**.
> Its replacement, the Creators API, requires 10 qualifying *affiliate sales* per
> rolling 30 days — that's an affiliate product, not suitable for a brand. SP-API
> is the correct route for a seller.

### Noon → Seller Lab API

Noon exposes a **Pricing API** for sellers to retrieve and update prices across
UAE / KSA / Egypt. Request API credentials through Seller Lab or your noon
partner/account manager.

### Noon Minutes / Talabat Mart

These are quick-commerce where the platform buys from you as a vendor. Ask your
account manager whether there's vendor-portal API access or a scheduled price
report — that's usually the only sanctioned route, and it's free.

**Credentials go in GitHub → Settings → Secrets and variables → Actions → Secrets.**
Never commit them.

---

## Path B (in use) — run it locally from a UAE IP

This is the current setup: you run `python -m scraper.local_run` on your own
machine, so requests come from a normal UAE address exactly like a customer.
Verified working — Amazon.ae returned AED 23.65 and both noon storefronts
returned real pages from this network, while GitHub's runners got challenges.

If you later want it scheduled without running it by hand, the same code can be
driven by a **self-hosted GitHub Actions runner** on an always-on UAE machine:

1. GitHub repo → **Settings → Actions → Runners → New self-hosted runner**
2. Follow the shown commands on the UAE machine
3. Install it as a service so it survives reboots:
   ```
   ./svc.sh install
   ./svc.sh start
   ```
4. Repo → **Settings → Secrets and variables → Actions → Variables** → new
   variable `RUNNER_LABEL` = `self-hosted`

Both workflows already read that variable (`runs-on: ${{ vars.RUNNER_LABEL || 'ubuntu-latest' }}`),
so nothing else needs changing. Unset the variable to switch back.

**Tradeoff:** a machine you own has to stay powered on. Nothing is *stored* on
it — the runner workspace is temporary and all data is still committed to this
repo, so the "everything lives in GitHub" requirement still holds.

> Security note: this repo is public. Self-hosted runners on public repos are
> risky if you ever accept outside pull requests, because PR code would execute
> on your machine. Either keep the repo free of untrusted PRs, or make the repo
> private (needs GitHub Pro for Pages) before enabling a self-hosted runner.
