const REPO_OWNER = "ecommerce1-cloud";
const REPO_NAME = "UAE-Pricing-Tracker";
const BRANCH = "main";
const TRACKED_PATH = "docs/data/tracked-products.json";
const TOKEN_STORAGE_KEY = "uae_tracker_pat";
const API_BASE = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}`;

function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY) || "";
}

function setToken(token) {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function ghHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

function b64EncodeUnicode(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

function b64DecodeUnicode(str) {
  return decodeURIComponent(escape(atob(str)));
}

async function fetchTrackedFile(token) {
  const res = await fetch(`${API_BASE}/contents/${TRACKED_PATH}?ref=${BRANCH}`, {
    headers: ghHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to read tracked-products.json (${res.status})`);
  const data = await res.json();
  const content = JSON.parse(b64DecodeUnicode(data.content));
  return { content, sha: data.sha };
}

async function commitTrackedFile(token, content, sha, message) {
  const res = await fetch(`${API_BASE}/contents/${TRACKED_PATH}`, {
    method: "PUT",
    headers: { ...ghHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      content: b64EncodeUnicode(JSON.stringify(content, null, 2)),
      sha,
      branch: BRANCH,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`Failed to commit tracked-products.json (${res.status}): ${err.message || ""}`);
  }
}

async function triggerOnDemandScrape(token, barcode) {
  const res = await fetch(`${API_BASE}/actions/workflows/on-demand-scrape.yml/dispatches`, {
    method: "POST",
    headers: { ...ghHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ ref: BRANCH, inputs: { barcode } }),
  });
  return res.ok;
}

function buildPlatformRefs(form) {
  const refs = {};

  const amazonRef = parseRef(form.amazon.value.trim());
  if (amazonRef) {
    refs.amazon_core = amazonRef;
    refs.amazon_fast = amazonRef; // reuses the same product page
  }

  const noonRef = parseRef(form.noon.value.trim());
  if (noonRef) refs.noon_retail = noonRef;

  const noonMinutesRef = parseRef(form.noon_minutes.value.trim());
  if (noonMinutesRef) refs.noon_minutes = noonMinutesRef;

  const talabatUrl = form.talabat.value.trim();
  if (talabatUrl) refs.talabat_mart = { url: talabatUrl };

  return refs;
}

// Accepts either a full URL or a bare ID (ASIN/SKU) and returns the right ref shape.
function parseRef(value) {
  if (!value) return null;
  if (value.startsWith("http")) return { url: value };
  return { asin: value, sku: value };
}

async function handleSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const statusEl = document.getElementById("status");
  const token = getToken();

  if (!token) {
    statusEl.textContent = "Save your GitHub token above first.";
    statusEl.className = "status error";
    return;
  }

  const barcode = form.barcode.value.trim();
  const name = form.name.value.trim();
  const platforms = buildPlatformRefs(form);

  if (!barcode || Object.keys(platforms).length === 0) {
    statusEl.textContent = "Barcode and at least one platform reference are required.";
    statusEl.className = "status error";
    return;
  }

  statusEl.textContent = "Saving to GitHub...";
  statusEl.className = "status";

  try {
    const { content, sha } = await fetchTrackedFile(token);
    content[barcode] = {
      name,
      added_at: new Date().toISOString(),
      platforms,
    };
    await commitTrackedFile(token, content, sha, `Add barcode ${barcode} via dashboard`);

    statusEl.textContent = "Saved. Triggering an immediate price check...";
    const triggered = await triggerOnDemandScrape(token, barcode);
    statusEl.textContent = triggered
      ? "Saved and price check triggered — refresh the dashboard in a minute or two."
      : "Saved, but couldn't auto-trigger a price check (check token has 'Actions: write'). It'll pick up on tomorrow's scheduled run.";
    statusEl.className = "status success";
    form.reset();
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = "status error";
  }
}

function initTokenForm() {
  const tokenInput = document.getElementById("token-input");
  const saveBtn = document.getElementById("save-token-btn");
  const forgetBtn = document.getElementById("forget-token-btn");
  const tokenStatus = document.getElementById("token-status");

  function refresh() {
    const has = !!getToken();
    tokenStatus.textContent = has ? "Token saved in this browser." : "No token saved yet.";
    tokenInput.value = "";
  }

  saveBtn.addEventListener("click", () => {
    setToken(tokenInput.value.trim());
    refresh();
  });
  forgetBtn.addEventListener("click", () => {
    setToken("");
    refresh();
  });
  refresh();
}

document.getElementById("add-product-form").addEventListener("submit", handleSubmit);
initTokenForm();
