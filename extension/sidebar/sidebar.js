/**
 * sidebar.js — Research sidebar logic.
 *
 * Displays niche data, competitor info, and BSR history for the
 * currently viewed Amazon product.
 */

// DOM refs
const productSection = document.getElementById("product-section");
const bsrHistorySection = document.getElementById("bsr-history-section");
const keywordsSection = document.getElementById("keywords-section");
const loadingEl = document.getElementById("loading");
const noDataEl = document.getElementById("no-data");

const productTitle = document.getElementById("product-title");
const productAsin = document.getElementById("product-asin");
const metricBsr = document.getElementById("metric-bsr");
const metricSales = document.getElementById("metric-sales");
const metricPrice = document.getElementById("metric-price");
const metricCompetitors = document.getElementById("metric-competitors");
const bsrHistoryBody = document.getElementById("bsr-history-body");
const keywordTagsEl = document.getElementById("keyword-tags");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatNumber(num) {
  if (num === null || num === undefined) return "--";
  return num.toLocaleString();
}

function showElement(el) {
  el.classList.remove("hidden");
}

function hideElement(el) {
  el.classList.add("hidden");
}

function sendBackgroundMessage(action, payload = {}) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ action, ...payload }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

function renderResearchData(data) {
  hideElement(loadingEl);
  hideElement(noDataEl);

  // Product info
  if (data.title || data.asin) {
    productTitle.textContent = data.title || "Unknown Product";
    productAsin.textContent = data.asin ? `ASIN: ${data.asin}` : "";
    showElement(productSection);
  }

  // Metrics
  metricBsr.textContent = formatNumber(data.current_bsr);
  metricSales.textContent = formatNumber(data.estimated_daily_sales);
  metricPrice.textContent = data.avg_price != null ? `$${data.avg_price.toFixed(2)}` : "--";
  metricCompetitors.textContent = formatNumber(data.competitor_count);

  // BSR history
  if (data.bsr_history && data.bsr_history.length > 0) {
    bsrHistoryBody.innerHTML = "";
    for (const entry of data.bsr_history) {
      const row = document.createElement("tr");
      const dateCell = document.createElement("td");
      const bsrCell = document.createElement("td");
      dateCell.textContent = entry.date
        ? new Date(entry.date).toLocaleDateString()
        : "--";
      bsrCell.textContent = formatNumber(entry.bsr);
      row.appendChild(dateCell);
      row.appendChild(bsrCell);
      bsrHistoryBody.appendChild(row);
    }
    showElement(bsrHistorySection);
  }

  // Keywords
  if (data.related_keywords && data.related_keywords.length > 0) {
    keywordTagsEl.innerHTML = "";
    for (const kw of data.related_keywords) {
      const span = document.createElement("span");
      span.className = "keyword-tag";
      span.textContent = kw;
      keywordTagsEl.appendChild(span);
    }
    showElement(keywordsSection);
  }
}

function showNoData() {
  hideElement(loadingEl);
  showElement(noDataEl);
}

// ---------------------------------------------------------------------------
// Initialise
// ---------------------------------------------------------------------------

async function init() {
  try {
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
      showNoData();
      return;
    }

    // Check if on Amazon product page
    const asinMatch = tab.url.match(/\/dp\/([A-Z0-9]{10})/i);
    if (!asinMatch) {
      showNoData();
      return;
    }

    const asin = asinMatch[1];

    // Fetch quick research from background/API
    const res = await sendBackgroundMessage("quickResearch", { asin });
    if (res && res.success && res.data) {
      renderResearchData(res.data);
    } else {
      // Even without API data, show what we can from the tab
      renderResearchData({ asin, title: tab.title });
    }
  } catch (err) {
    console.error("SPF Sidebar error:", err);
    showNoData();
  }
}

document.addEventListener("DOMContentLoaded", init);
