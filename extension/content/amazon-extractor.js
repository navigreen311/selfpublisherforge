/**
 * amazon-extractor.js — Content script for Amazon product pages.
 *
 * Extracts product data from the DOM: title, BSR, price, reviews,
 * categories, keywords, ASIN, and more.
 *
 * Listens for messages from the popup or background to trigger extraction.
 */

// ---------------------------------------------------------------------------
// Marketplace detection
// ---------------------------------------------------------------------------

function detectMarketplace() {
  const host = window.location.hostname;
  const marketplaceMap = {
    "www.amazon.com": "amazon.com",
    "www.amazon.co.uk": "amazon.co.uk",
    "www.amazon.de": "amazon.de",
    "www.amazon.fr": "amazon.fr",
    "www.amazon.ca": "amazon.ca",
    "www.amazon.com.au": "amazon.com.au",
    "www.amazon.co.jp": "amazon.co.jp",
    "www.amazon.it": "amazon.it",
    "www.amazon.es": "amazon.es",
    "www.amazon.in": "amazon.in",
  };
  return marketplaceMap[host] || "amazon.com";
}

// ---------------------------------------------------------------------------
// ASIN extraction
// ---------------------------------------------------------------------------

function extractASIN() {
  // Try the canonical URL first
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) {
    const match = canonical.href.match(/\/dp\/([A-Z0-9]{10})/i);
    if (match) return match[1];
  }

  // Try the URL path
  const urlMatch = window.location.pathname.match(/\/dp\/([A-Z0-9]{10})/i);
  if (urlMatch) return urlMatch[1];

  // Try hidden input
  const input = document.querySelector('input[name="ASIN"]');
  if (input) return input.value;

  // Try data attribute
  const asinEl = document.querySelector("[data-asin]");
  if (asinEl) return asinEl.getAttribute("data-asin");

  return null;
}

// ---------------------------------------------------------------------------
// Title
// ---------------------------------------------------------------------------

function extractTitle() {
  const el =
    document.getElementById("productTitle") ||
    document.querySelector("#title span") ||
    document.querySelector("h1.a-size-large");
  return el ? el.textContent.trim() : null;
}

// ---------------------------------------------------------------------------
// Subtitle
// ---------------------------------------------------------------------------

function extractSubtitle() {
  const el = document.getElementById("productSubtitle");
  return el ? el.textContent.trim() : null;
}

// ---------------------------------------------------------------------------
// Author
// ---------------------------------------------------------------------------

function extractAuthor() {
  // Kindle / book author
  const byLine = document.querySelector(".contributorNameID, #bylineInfo .author a, .author .a-link-normal");
  if (byLine) return byLine.textContent.trim();

  const bylineInfo = document.getElementById("bylineInfo");
  if (bylineInfo) {
    const authorLink = bylineInfo.querySelector("a.contributorNameID, a");
    if (authorLink) return authorLink.textContent.trim();
  }

  return null;
}

// ---------------------------------------------------------------------------
// Price
// ---------------------------------------------------------------------------

function extractPrice() {
  // Try Kindle price
  const priceSpan =
    document.querySelector("#kindle-price, .kindle-price .a-color-price") ||
    document.querySelector("#price .a-color-price") ||
    document.querySelector(".a-price .a-offscreen") ||
    document.querySelector("#priceblock_ourprice") ||
    document.querySelector("#priceblock_dealprice");

  if (priceSpan) {
    const raw = priceSpan.textContent.trim();
    const num = parseFloat(raw.replace(/[^0-9.]/g, ""));
    if (!isNaN(num)) return num;
  }
  return null;
}

function extractCurrency() {
  const priceEl = document.querySelector(".a-price-symbol");
  if (priceEl) {
    const symbol = priceEl.textContent.trim();
    const map = { "$": "USD", "\u00a3": "GBP", "\u20ac": "EUR", "\u00a5": "JPY", "CA$": "CAD", "A$": "AUD" };
    return map[symbol] || "USD";
  }
  return "USD";
}

// ---------------------------------------------------------------------------
// BSR (Best Sellers Rank)
// ---------------------------------------------------------------------------

/**
 * Parse a BSR text block and extract overall rank + category ranks.
 *
 * Handles multiple Amazon BSR formats:
 *   "#1,234 in Books"
 *   "#1,234 in Kindle Store (See Top 100 …)"
 *   "#42 in Kindle eBooks > Romance > Contemporary"
 *   "Nr. 1.234 in …" (DE locale with period separator)
 *
 * @param {string} text  The raw text containing BSR information.
 * @param {number|null} currentOverallBSR  Previously found overall BSR (if any).
 * @param {Object} bsrCategories  Accumulator for category ranks.
 * @returns {{ overallBSR: number|null, bsrCategories: Object }}
 */
function _parseBSRText(text, currentOverallBSR, bsrCategories) {
  let overallBSR = currentOverallBSR;

  // Regex patterns for different BSR formats across locales
  const rankPatterns = [
    // Standard: "#1,234 in Books" or "#1,234 in Kindle Store"
    /#([\d,]+)\s+in\s+([^\n(#]+)/g,
    // German / EU locale: "Nr. 1.234 in …"
    /Nr\.\s*([\d.]+)\s+in\s+([^\n(#]+)/gi,
    // Compact: "#1234in Books" (some mobile layouts omit the space)
    /#([\d,]+)in\s+([^\n(#]+)/g,
  ];

  for (const pattern of rankPatterns) {
    // Reset lastIndex in case the regex was previously used
    pattern.lastIndex = 0;
    const matches = text.matchAll(pattern);
    for (const m of matches) {
      const rank = parseInt(m[1].replace(/[,.\s]/g, ""), 10);
      const cat = m[2].trim().replace(/\s*\(.*$/, "").replace(/\s+$/, "");
      if (cat && rank > 0) {
        bsrCategories[cat] = rank;
        // First match is the overall/broadest rank
        if (!overallBSR) {
          overallBSR = rank;
        }
      }
    }
  }

  // Fallback: just grab the first "#<number>" if nothing matched above
  if (!overallBSR) {
    const simpleMatch = text.match(/#([\d,]+)/);
    if (simpleMatch) {
      overallBSR = parseInt(simpleMatch[1].replace(/,/g, ""), 10);
    }
  }

  return { overallBSR, bsrCategories };
}

function extractBSR() {
  let overallBSR = null;
  const bsrCategories = {};

  // -----------------------------------------------------------------------
  // Strategy 1: Product details table (most common modern layout)
  // Selector: #productDetails_detailBullets_sections1 table rows
  // -----------------------------------------------------------------------
  try {
    const tableRows = document.querySelectorAll(
      "#productDetails_detailBullets_sections1 tr"
    );
    for (const row of tableRows) {
      const text = row.textContent;
      if (/best\s*sellers?\s*rank/i.test(text)) {
        const parsed = _parseBSRText(text, overallBSR, bsrCategories);
        overallBSR = parsed.overallBSR;
      }
    }
  } catch (e) {
    /* selector may not exist — continue to fallbacks */
  }

  // -----------------------------------------------------------------------
  // Strategy 2: Detail bullets wrapper (alternate layout)
  // Selector: #detailBulletsWrapper_feature_div list items
  // -----------------------------------------------------------------------
  if (!overallBSR) {
    try {
      const wrapperItems = document.querySelectorAll(
        "#detailBulletsWrapper_feature_div li"
      );
      for (const item of wrapperItems) {
        const text = item.textContent;
        if (/best\s*sellers?\s*rank/i.test(text)) {
          const parsed = _parseBSRText(text, overallBSR, bsrCategories);
          overallBSR = parsed.overallBSR;
        }
      }
    } catch (e) {
      /* continue */
    }
  }

  // -----------------------------------------------------------------------
  // Strategy 3: Detail bullets feature div (older layout variant)
  // Selector: #detailBullets_feature_div .a-list-item
  // -----------------------------------------------------------------------
  if (!overallBSR) {
    try {
      const bullets = document.querySelectorAll(
        "#detailBullets_feature_div .a-list-item"
      );
      for (const bullet of bullets) {
        const text = bullet.textContent;
        if (/best\s*sellers?\s*rank/i.test(text)) {
          const parsed = _parseBSRText(text, overallBSR, bsrCategories);
          overallBSR = parsed.overallBSR;
        }
      }
    } catch (e) {
      /* continue */
    }
  }

  // -----------------------------------------------------------------------
  // Strategy 4: .prodDetTable (older/legacy product detail layout)
  // -----------------------------------------------------------------------
  if (!overallBSR) {
    try {
      const prodDetCells = document.querySelectorAll(".prodDetTable td");
      for (const cell of prodDetCells) {
        const text = cell.textContent;
        if (/best\s*sellers?\s*rank/i.test(text)) {
          const parsed = _parseBSRText(text, overallBSR, bsrCategories);
          overallBSR = parsed.overallBSR;
        }
      }
    } catch (e) {
      /* continue */
    }
  }

  // -----------------------------------------------------------------------
  // Strategy 5: Broad sweep — look for "Best Sellers Rank" text anywhere
  // within known product-information containers. This catches edge-case
  // layouts and A/B tests Amazon may be running.
  // -----------------------------------------------------------------------
  if (!overallBSR) {
    try {
      const containers = [
        "#productDetails_feature_div",
        "#detailBulletsWrapper_feature_div",
        "#prodDetails",
        "#detail-bullets",
        "#bookDescription_feature_div",
      ];
      for (const sel of containers) {
        const el = document.querySelector(sel);
        if (!el) continue;
        const text = el.textContent || "";
        if (/best\s*sellers?\s*rank/i.test(text)) {
          const parsed = _parseBSRText(text, overallBSR, bsrCategories);
          overallBSR = parsed.overallBSR;
          if (overallBSR) break;
        }
      }
    } catch (e) {
      /* continue */
    }
  }

  // -----------------------------------------------------------------------
  // Strategy 6: Last resort — scan all <th> and <span> elements for the
  // label "Best Sellers Rank" and read the adjacent sibling / parent row.
  // -----------------------------------------------------------------------
  if (!overallBSR) {
    try {
      const candidates = document.querySelectorAll("th, span.a-text-bold");
      for (const node of candidates) {
        if (/best\s*sellers?\s*rank/i.test(node.textContent)) {
          // Grab the nearest row or parent element for context
          const context = node.closest("tr") || node.parentElement;
          if (context) {
            const parsed = _parseBSRText(context.textContent, overallBSR, bsrCategories);
            overallBSR = parsed.overallBSR;
            if (overallBSR) break;
          }
        }
      }
    } catch (e) {
      /* continue */
    }
  }

  return { bsr: overallBSR, bsr_categories: bsrCategories };
}

// ---------------------------------------------------------------------------
// Reviews
// ---------------------------------------------------------------------------

function extractReviews() {
  const result = { total_reviews: 0, average_rating: null, rating_distribution: {} };

  // Total reviews count
  const countEl = document.getElementById("acrCustomerReviewCount");
  if (countEl) {
    const match = countEl.textContent.match(/([\d,]+)/);
    if (match) result.total_reviews = parseInt(match[1].replace(/,/g, ""), 10);
  }

  // Average rating
  const ratingEl = document.querySelector("#acrPopover .a-icon-alt, .reviewCountTextLinkedHistogram .a-icon-alt");
  if (ratingEl) {
    const match = ratingEl.textContent.match(/([\d.]+)/);
    if (match) result.average_rating = parseFloat(match[1]);
  }

  // Rating distribution (histogram)
  const histogramRows = document.querySelectorAll("#histogramTable tr, .a-histogram-row");
  for (const row of histogramRows) {
    const starMatch = row.textContent.match(/(\d)\s*star/i);
    const pctMatch = row.textContent.match(/(\d+)%/);
    if (starMatch && pctMatch) {
      result.rating_distribution[starMatch[1]] = parseInt(pctMatch[1], 10);
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Categories (breadcrumbs)
// ---------------------------------------------------------------------------

function extractCategories() {
  const crumbs = document.querySelectorAll(
    "#wayfinding-breadcrumbs_feature_div a, .a-breadcrumb a"
  );
  return Array.from(crumbs).map((a) => a.textContent.trim()).filter(Boolean);
}

// ---------------------------------------------------------------------------
// Keywords (from page metadata)
// ---------------------------------------------------------------------------

function extractKeywords() {
  const metaKw = document.querySelector('meta[name="keywords"]');
  if (metaKw) {
    return metaKw.content
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
  }
  return [];
}

// ---------------------------------------------------------------------------
// Additional fields
// ---------------------------------------------------------------------------

function extractImageUrl() {
  const img =
    document.getElementById("imgBlkFront") ||
    document.getElementById("ebooksImgBlkFront") ||
    document.querySelector("#imageBlock img") ||
    document.querySelector("#main-image");
  return img ? img.src : null;
}

function extractBookDetails() {
  const details = { publication_date: null, page_count: null, language: null, dimensions: null, isbn: null };

  const rows = document.querySelectorAll(
    "#productDetails_detailBullets_sections1 tr, #detailBulletsWrapper_feature_div li, #rpiStrip498_feature_div .rpi-attribute-value"
  );

  for (const row of rows) {
    const text = row.textContent.toLowerCase();
    const value = row.querySelector("td:last-child, .a-list-item span:last-child");
    const val = value ? value.textContent.trim() : row.textContent.trim();

    if (/publication date|publisher/.test(text)) {
      const dateMatch = val.match(/\w+\s+\d{1,2},?\s*\d{4}/);
      if (dateMatch) details.publication_date = dateMatch[0];
    }
    if (/page/.test(text) && /\d+/.test(val)) {
      const num = parseInt(val.match(/\d+/)[0], 10);
      if (num > 0 && num < 50000) details.page_count = num;
    }
    if (/language/.test(text)) {
      details.language = val.replace(/[^a-zA-Z\s]/g, "").trim() || null;
    }
    if (/dimension/.test(text)) {
      details.dimensions = val;
    }
    if (/isbn-?1[03]/i.test(text)) {
      const isbnMatch = val.match(/[\dX-]{10,17}/i);
      if (isbnMatch) details.isbn = isbnMatch[0];
    }
  }

  return details;
}

// ---------------------------------------------------------------------------
// Full extraction
// ---------------------------------------------------------------------------

function extractProductData() {
  const asin = extractASIN();
  if (!asin) return null;

  const bsrData = extractBSR();
  const bookDetails = extractBookDetails();

  return {
    asin,
    title: extractTitle() || "Unknown Title",
    subtitle: extractSubtitle(),
    author: extractAuthor(),
    price: extractPrice(),
    currency: extractCurrency(),
    bsr: bsrData.bsr,
    bsr_categories: bsrData.bsr_categories,
    categories: extractCategories(),
    keywords: extractKeywords(),
    reviews: extractReviews(),
    page_url: window.location.href,
    image_url: extractImageUrl(),
    marketplace: detectMarketplace(),
    publication_date: bookDetails.publication_date,
    page_count: bookDetails.page_count,
    language: bookDetails.language,
    dimensions: bookDetails.dimensions,
    isbn: bookDetails.isbn,
  };
}

// ---------------------------------------------------------------------------
// Message listener
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "extractData") {
    const data = extractProductData();
    sendResponse({ data });
    return true; // keep channel open for async
  }

  if (message.action === "getSelection") {
    const text = window.getSelection()?.toString() || "";
    sendResponse({ text });
    return true;
  }

  if (message.action === "toggleSidebar") {
    toggleSidebarOverlay();
    sendResponse({ success: true });
    return true;
  }

  return false;
});

// ---------------------------------------------------------------------------
// Sidebar overlay fallback (injected iframe)
// ---------------------------------------------------------------------------

let sidebarFrame = null;

function toggleSidebarOverlay() {
  if (sidebarFrame) {
    sidebarFrame.remove();
    sidebarFrame = null;
    return;
  }

  sidebarFrame = document.createElement("iframe");
  sidebarFrame.src = chrome.runtime.getURL("sidebar/sidebar.html");
  sidebarFrame.id = "spf-sidebar-frame";
  Object.assign(sidebarFrame.style, {
    position: "fixed",
    top: "0",
    right: "0",
    width: "380px",
    height: "100vh",
    border: "none",
    zIndex: "2147483647",
    boxShadow: "-4px 0 20px rgba(0,0,0,0.15)",
    background: "#fff",
  });
  document.body.appendChild(sidebarFrame);
}

// Auto-extract on load and notify background (optional badge update)
(function autoDetect() {
  const data = extractProductData();
  if (data) {
    chrome.runtime.sendMessage({ action: "pageDetected", data });
  }
})();
