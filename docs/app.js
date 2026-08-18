const ZONE_NAME_BY_ID = Object.fromEntries(ZONES.map((z) => [z.id, z.name]));

let latestData = {};
let trackedData = {};

async function loadData() {
  const [trackedRes, latestRes] = await Promise.all([
    fetch("data/tracked-products.json", { cache: "no-store" }),
    fetch("data/latest-prices.json", { cache: "no-store" }),
  ]);
  trackedData = await trackedRes.json();
  latestData = await latestRes.json();
}

function escapeAttr(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// An empty cell means one of two very different things: the platform refused the
// request (infrastructure problem -- shows a warning) or the product just isn't
// sold/tracked there (plain dash). Either way the reason goes in the tooltip.
function unavailableCell(errorMsg) {
  const blocked = /^blocked:/i.test(errorMsg || "");
  const glyph = blocked ? "⚠" : "—";
  const cls = blocked ? "price unavailable blocked" : "price unavailable";
  return `<span class="${cls}" title="${escapeAttr(errorMsg || "no data yet")}">${glyph}</span>`;
}

function formatPrice(priceData) {
  if (!priceData || !priceData.available || priceData.price == null) {
    return unavailableCell(priceData && priceData.error);
  }
  return `<span class="price">AED ${priceData.price.toFixed(2)}</span>`;
}

function renderZoneCell(platformId, zoneResults) {
  const perZone = ZONES.map((z) => zoneResults[z.id]);
  const available = perZone.filter((r) => r && r.available && r.price != null);

  if (available.length === 0) {
    const firstErr = perZone.find((r) => r && r.error);
    return `<div class="price-cell">${unavailableCell(firstErr && firstErr.error)}</div>`;
  }

  const prices = available.map((r) => r.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const summary =
    min === max
      ? `<span class="price">AED ${min.toFixed(2)}</span>`
      : `<span class="price">AED ${min.toFixed(2)}–${max.toFixed(2)}</span>`;

  const cellId = `zones-${platformId}-${Math.random().toString(36).slice(2)}`;
  const breakdown = ZONES.map((z) => {
    const r = zoneResults[z.id];
    const text =
      r && r.available && r.price != null
        ? `AED ${r.price.toFixed(2)}`
        : unavailableCell(r && r.error);
    return `<div><span>${z.name}</span><span>${text}</span></div>`;
  }).join("");

  const label = available.length === ZONES.length ? "5 zones" : `${available.length}/${ZONES.length} zones`;

  return `
    <div class="price-cell">
      ${summary}
      <span class="zone-toggle" onclick="document.getElementById('${cellId}').classList.toggle('hidden')">${label} ▾</span>
      <div class="zone-breakdown hidden" id="${cellId}">${breakdown}</div>
    </div>
  `;
}

function renderTable() {
  const barcodes = Object.keys(trackedData);
  const tbody = document.getElementById("price-tbody");
  const emptyState = document.getElementById("empty-state");
  const tableWrap = document.getElementById("table-wrap");

  if (barcodes.length === 0) {
    tableWrap.classList.add("hidden");
    emptyState.classList.remove("hidden");
    return;
  }
  tableWrap.classList.remove("hidden");
  emptyState.classList.add("hidden");

  tbody.innerHTML = barcodes
    .map((barcode) => {
      const product = trackedData[barcode];
      const latest = latestData[barcode];
      const platformCells = PLATFORMS.map((platform) => {
        const platformResult = latest && latest.platforms ? latest.platforms[platform.id] : null;
        if (!platformResult) {
          return `<td class="price-cell">${unavailableCell("not tracked on this platform")}</td>`;
        }
        if (platform.zoneBased) {
          return `<td>${renderZoneCell(platform.id, platformResult.zones || {})}</td>`;
        }
        return `<td class="price-cell">${formatPrice(platformResult)}</td>`;
      }).join("");

      const checkedAt = latest ? new Date(latest.checked_at).toLocaleString("en-AE") : "never";

      return `
        <tr>
          <td class="barcode-cell">${barcode}</td>
          <td>
            <span class="product-name">${product.name || "(unnamed)"}</span>
            <span class="checked-at">Checked: ${checkedAt}</span>
          </td>
          ${platformCells}
        </tr>
      `;
    })
    .join("");
}

function renderHeader() {
  const headRow = document.getElementById("platform-head-row");
  headRow.innerHTML =
    `<th>Barcode</th><th>Product</th>` +
    PLATFORMS.map(
      (p) => `
      <th>
        <div class="platform-header">
          <img src="${p.logo}" alt="${p.name} logo" />
          <span>${p.name}</span>
        </div>
      </th>`
    ).join("");
}

function exportCSV() {
  const rows = [
    ["barcode", "product_name", "platform", "zone", "price", "currency", "available", "note", "checked_at"],
  ];

  for (const [barcode, product] of Object.entries(trackedData)) {
    const latest = latestData[barcode];
    if (!latest) continue;
    for (const platform of PLATFORMS) {
      const result = latest.platforms ? latest.platforms[platform.id] : null;
      if (!result) continue;
      if (platform.zoneBased) {
        for (const zone of ZONES) {
          const r = result.zones ? result.zones[zone.id] : null;
          rows.push([
            barcode,
            product.name || "",
            platform.name,
            zone.name,
            r && r.price != null ? r.price : "",
            r ? r.currency : "",
            r ? r.available : "",
            r && r.error ? r.error : "",
            latest.checked_at,
          ]);
        }
      } else {
        rows.push([
          barcode,
          product.name || "",
          platform.name,
          "",
          result.price != null ? result.price : "",
          result.currency,
          result.available,
          result.error || "",
          latest.checked_at,
        ]);
      }
    }
  }

  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `uae-price-tracker-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function init() {
  renderHeader();
  if (window.DEMO_DATA) {
    trackedData = window.DEMO_DATA.tracked;
    latestData = window.DEMO_DATA.latest;
  } else {
    await loadData();
  }
  renderTable();
  document.getElementById("export-btn").addEventListener("click", exportCSV);
}

init();
