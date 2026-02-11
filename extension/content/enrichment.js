/**
 * enrichment.js — Additional Amazon metadata extraction.
 *
 * Extracts deeper product metadata:
 * - Also-bought / Frequently bought together
 * - Editorial reviews (back cover, about author, publisher description)
 * - Extended book details (publisher, print length, reading age, item weight, all BSR categories)
 * - Customer Q&A
 * - Look Inside availability
 * - Series information
 * - Kindle-specific features (KU, price comparison, Page Flip, X-Ray, Word Wise)
 */

// ---------------------------------------------------------------------------
// Also-Bought / Frequently Bought Together
// ---------------------------------------------------------------------------

/**
 * Extract products from the "Frequently bought together" section.
 * Returns an array of { asin, title } objects.
 */
function extractFrequentlyBoughtTogether() {
  const products = [];

  try {
    // Strategy 1: Modern carousel layout
    const carouselItems = document.querySelectorAll(
      "#sims-fbt .a-carousel-card, #sims-fbt .sims-fbt-image, #similarities_feature_div .a-carousel-card"
    );

    for (const item of carouselItems) {
      const link = item.querySelector("a[href*='/dp/']");
      if (link) {
        const match = link.href.match(/\/dp\/([A-Z0-9]{10})/i);
        const titleEl = item.querySelector(".a-size-base, .a-link-normal") || link;
        if (match) {
          products.push({
            asin: match[1],
            title: titleEl.textContent.trim() || null,
          });
        }
      }
    }

    // Strategy 2: Legacy grid layout
    if (products.length === 0) {
      const fbtContainer = document.querySelector("#sims-fbt, #similarities_feature_div");
      if (fbtContainer) {
        const links = fbtContainer.querySelectorAll("a[href*='/dp/']");
        for (const link of links) {
          const match = link.href.match(/\/dp\/([A-Z0-9]{10})/i);
          if (match && !products.find((p) => p.asin === match[1])) {
            products.push({
              asin: match[1],
              title: link.textContent.trim() || null,
            });
          }
        }
      }
    }

    // Strategy 3: Data attributes
    if (products.length === 0) {
      const dataItems = document.querySelectorAll("[data-asin]");
      const fbtSection = document.querySelector("#sims-fbt, #similarities_feature_div");
      if (fbtSection) {
        for (const item of fbtSection.querySelectorAll("[data-asin]")) {
          const asin = item.getAttribute("data-asin");
          if (asin && asin.length === 10) {
            const titleEl = item.querySelector(".a-size-base, .a-link-normal");
            products.push({
              asin,
              title: titleEl ? titleEl.textContent.trim() : null,
            });
          }
        }
      }
    }
  } catch (e) {
    console.warn("Error extracting frequently bought together:", e);
  }

  // Deduplicate by ASIN
  const seen = new Set();
  return products.filter((p) => {
    if (seen.has(p.asin)) return false;
    seen.add(p.asin);
    return true;
  });
}

// ---------------------------------------------------------------------------
// Editorial Reviews
// ---------------------------------------------------------------------------

/**
 * Extract editorial reviews including:
 * - From the Back Cover
 * - About the Author
 * - Publisher description
 */
function extractEditorialReviews() {
  const reviews = {
    backCover: null,
    aboutAuthor: null,
    publisherDescription: null,
  };

  try {
    // Strategy 1: Book description feature div
    const bookDesc = document.querySelector("#bookDescription_feature_div, #editorialReviews_feature_div");
    if (bookDesc) {
      const sections = bookDesc.querySelectorAll(".a-section, .content");

      for (const section of sections) {
        const heading = section.querySelector("h3, .a-text-bold, b");
        const headingText = heading ? heading.textContent.toLowerCase() : "";
        const content = section.querySelector("p, .a-expander-content, noscript");

        if (content) {
          const text = content.textContent.trim();
          if (text.length > 20) {
            if (/back\s*cover/i.test(headingText)) {
              reviews.backCover = text;
            } else if (/about\s*(the\s*)?author/i.test(headingText)) {
              reviews.aboutAuthor = text;
            } else if (/publisher|description|from\s*the\s*publisher/i.test(headingText)) {
              reviews.publisherDescription = text;
            }
          }
        }
      }
    }

    // Strategy 2: Product description div
    if (!reviews.publisherDescription) {
      const productDesc = document.querySelector(
        "#productDescription p, #productDescription .content, #productDescription_feature_div .a-expander-content"
      );
      if (productDesc) {
        const text = productDesc.textContent.trim();
        if (text.length > 20) {
          reviews.publisherDescription = text;
        }
      }
    }

    // Strategy 3: Feature bullets (sometimes used for description)
    if (!reviews.publisherDescription) {
      const featureBullets = document.querySelector("#feature-bullets, #featurebullets_feature_div");
      if (featureBullets) {
        const bullets = Array.from(featureBullets.querySelectorAll("li span"))
          .map((s) => s.textContent.trim())
          .filter((t) => t.length > 10);
        if (bullets.length > 0) {
          reviews.publisherDescription = bullets.join(" ");
        }
      }
    }

    // Strategy 4: About the Author fallback
    if (!reviews.aboutAuthor) {
      const authorSection = document.querySelector("#aboutTheAuthor, #author-profile");
      if (authorSection) {
        const text = authorSection.textContent.trim();
        if (text.length > 20) {
          reviews.aboutAuthor = text;
        }
      }
    }
  } catch (e) {
    console.warn("Error extracting editorial reviews:", e);
  }

  return reviews;
}

// ---------------------------------------------------------------------------
// Extended Book Details
// ---------------------------------------------------------------------------

/**
 * Extract additional book details beyond the basic extraction:
 * - Publisher name
 * - Print length
 * - Reading age
 * - Grade level
 * - Item weight
 */
function extractExtendedBookDetails() {
  const details = {
    publisher: null,
    printLength: null,
    readingAge: null,
    gradeLevel: null,
    itemWeight: null,
  };

  try {
    const rows = document.querySelectorAll(
      "#productDetails_detailBullets_sections1 tr, #detailBulletsWrapper_feature_div li, #detailBullets_feature_div .a-list-item"
    );

    for (const row of rows) {
      const text = row.textContent.toLowerCase();
      const value = row.querySelector("td:last-child, .a-list-item span:last-child");
      const val = value ? value.textContent.trim() : row.textContent.trim();

      if (/publisher\s*:/i.test(text) && !details.publisher) {
        // Extract publisher name (before the date/edition info)
        const match = val.match(/^([^;(]+)/);
        if (match) {
          details.publisher = match[1].trim();
        }
      }

      if (/print\s*length|number\s*of\s*pages/i.test(text) && !details.printLength) {
        const num = val.match(/(\d+)\s*pages?/i);
        if (num) {
          details.printLength = parseInt(num[1], 10);
        }
      }

      if (/reading\s*age/i.test(text) && !details.readingAge) {
        details.readingAge = val.replace(/[^\d\s-years]/gi, "").trim();
      }

      if (/grade\s*level/i.test(text) && !details.gradeLevel) {
        details.gradeLevel = val;
      }

      if (/item\s*weight|shipping\s*weight/i.test(text) && !details.itemWeight) {
        details.itemWeight = val;
      }
    }
  } catch (e) {
    console.warn("Error extracting extended book details:", e);
  }

  return details;
}

// ---------------------------------------------------------------------------
// Customer Q&A
// ---------------------------------------------------------------------------

/**
 * Extract top 3 customer questions and answers.
 * Returns an array of { question, answer } objects.
 */
function extractCustomerQA() {
  const qaList = [];

  try {
    // Strategy 1: Q&A section with structured elements
    const qaItems = document.querySelectorAll(
      "#ask .askTeaserQuestions .a-spacing-base, #ask-dp-search_feature_div .a-spacing-base, #ask-btf_feature_div .a-spacing-base"
    );

    for (const item of qaItems) {
      if (qaList.length >= 3) break;

      const questionEl = item.querySelector(".a-text-bold, .askQuestionText, a.a-link-normal");
      const answerEl = item.querySelector(".askAnswerText, .a-color-tertiary");

      if (questionEl) {
        qaList.push({
          question: questionEl.textContent.trim(),
          answer: answerEl ? answerEl.textContent.trim() : null,
        });
      }
    }

    // Strategy 2: Legacy Q&A layout
    if (qaList.length === 0) {
      const questions = document.querySelectorAll("#ask .a-fixed-left-grid");
      for (const q of questions) {
        if (qaList.length >= 3) break;

        const questionText = q.querySelector(".a-text-bold");
        const answerText = q.querySelector(".a-color-tertiary");

        if (questionText) {
          qaList.push({
            question: questionText.textContent.trim(),
            answer: answerText ? answerText.textContent.trim() : null,
          });
        }
      }
    }
  } catch (e) {
    console.warn("Error extracting customer Q&A:", e);
  }

  return qaList.slice(0, 3);
}

// ---------------------------------------------------------------------------
// Look Inside Availability
// ---------------------------------------------------------------------------

/**
 * Detect if the "Look Inside" feature is available for this book.
 * Returns true/false.
 */
function extractLookInsideAvailable() {
  try {
    // Strategy 1: Look Inside button/link
    const lookInsideBtn = document.querySelector(
      "#sitbLogoImg, #litb-canvas, .sample-image-button, a[href*='sitb-open'], img[alt*='Look Inside']"
    );
    if (lookInsideBtn) return true;

    // Strategy 2: Data attribute
    const bookReader = document.querySelector("[data-feature-name='bookReader']");
    if (bookReader) return true;

    // Strategy 3: Script injection check
    const scripts = document.querySelectorAll("script");
    for (const script of scripts) {
      if (script.textContent.includes("sitbReader") || script.textContent.includes("lookInside")) {
        return true;
      }
    }

    return false;
  } catch (e) {
    console.warn("Error detecting Look Inside:", e);
    return false;
  }
}

// ---------------------------------------------------------------------------
// Series Information
// ---------------------------------------------------------------------------

/**
 * Extract series information if the book is part of a series.
 * Returns { seriesName, bookNumber } or null.
 */
function extractSeriesInfo() {
  try {
    // Strategy 1: Explicit series link
    const seriesLink = document.querySelector(
      "#seriesTitle, #series-link, a[href*='/series/'], .series"
    );
    if (seriesLink) {
      const text = seriesLink.textContent.trim();
      const numberMatch = text.match(/book\s*(\d+)/i);
      return {
        seriesName: text.replace(/\(.*?\)/g, "").trim(),
        bookNumber: numberMatch ? parseInt(numberMatch[1], 10) : null,
      };
    }

    // Strategy 2: Subtitle or title contains series info
    const subtitle = document.getElementById("productSubtitle");
    if (subtitle) {
      const text = subtitle.textContent;
      const seriesMatch = text.match(/\(([^)]+series[^)]*)\)/i);
      const numberMatch = text.match(/book\s*(\d+)/i);
      if (seriesMatch) {
        return {
          seriesName: seriesMatch[1].trim(),
          bookNumber: numberMatch ? parseInt(numberMatch[1], 10) : null,
        };
      }
    }

    // Strategy 3: Product details section
    const rows = document.querySelectorAll(
      "#productDetails_detailBullets_sections1 tr, #detailBulletsWrapper_feature_div li"
    );
    for (const row of rows) {
      const text = row.textContent;
      if (/series/i.test(text)) {
        const value = row.querySelector("td:last-child, span:last-child");
        const val = value ? value.textContent.trim() : text;
        const numberMatch = val.match(/book\s*(\d+)/i);
        return {
          seriesName: val.replace(/\(.*?\)/g, "").trim(),
          bookNumber: numberMatch ? parseInt(numberMatch[1], 10) : null,
        };
      }
    }

    return null;
  } catch (e) {
    console.warn("Error extracting series info:", e);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Kindle-Specific Features
// ---------------------------------------------------------------------------

/**
 * Extract Kindle-specific metadata:
 * - Kindle Unlimited enrollment
 * - Kindle price vs print price comparison
 * - Page Flip enabled
 * - X-Ray enabled
 * - Word Wise enabled
 */
function extractKindleFeatures() {
  const features = {
    kindleUnlimited: false,
    kindlePrice: null,
    printPrice: null,
    pageFlip: false,
    xRay: false,
    wordWise: false,
  };

  try {
    // Kindle Unlimited
    const kuBadge = document.querySelector(
      "#kindle-unlimited-logo, img[alt*='Kindle Unlimited'], .ku-icon, a[href*='kindle-unlimited']"
    );
    if (kuBadge) {
      features.kindleUnlimited = true;
    }

    // Kindle price
    const kindlePriceEl = document.querySelector(
      "#kindle-price, .kindle-price .a-color-price, #ebooksKindlePrice .a-color-price"
    );
    if (kindlePriceEl) {
      const raw = kindlePriceEl.textContent.trim();
      const num = parseFloat(raw.replace(/[^0-9.]/g, ""));
      if (!isNaN(num)) features.kindlePrice = num;
    }

    // Print price (for comparison)
    const printPriceEl = document.querySelector(
      "#mediaTab_heading_1 .a-color-price, #tmmSwatches .a-color-price, .mediaTab_content .a-color-price"
    );
    if (printPriceEl) {
      const raw = printPriceEl.textContent.trim();
      const num = parseFloat(raw.replace(/[^0-9.]/g, ""));
      if (!isNaN(num)) features.printPrice = num;
    }

    // Page Flip
    const pageFlipEl = document.querySelector(".pageFlip, [data-feature-name='pageFlip']");
    if (pageFlipEl || document.body.textContent.includes("Page Flip")) {
      features.pageFlip = true;
    }

    // X-Ray
    const xRayEl = document.querySelector(".xRay, [data-feature-name='xRay']");
    if (xRayEl || /x-ray\s*:/i.test(document.body.textContent)) {
      features.xRay = true;
    }

    // Word Wise
    const wordWiseEl = document.querySelector(".wordWise, [data-feature-name='wordWise']");
    if (wordWiseEl || /word\s*wise\s*:/i.test(document.body.textContent)) {
      features.wordWise = true;
    }

    // Alternative: check product details for Kindle features
    const rows = document.querySelectorAll(
      "#productDetails_detailBullets_sections1 tr, #detailBulletsWrapper_feature_div li, #detailBullets_feature_div .a-list-item"
    );
    for (const row of rows) {
      const text = row.textContent.toLowerCase();
      if (text.includes("page flip") && /enabled|yes/i.test(text)) {
        features.pageFlip = true;
      }
      if (text.includes("x-ray") && /enabled|yes/i.test(text)) {
        features.xRay = true;
      }
      if (text.includes("word wise") && /enabled|yes/i.test(text)) {
        features.wordWise = true;
      }
    }
  } catch (e) {
    console.warn("Error extracting Kindle features:", e);
  }

  return features;
}

// ---------------------------------------------------------------------------
// Main enrichment function
// ---------------------------------------------------------------------------

/**
 * Extract all enrichment data and return as a single object.
 * Can be called independently or integrated with main extraction.
 */
function extractEnrichmentData() {
  return {
    frequentlyBoughtTogether: extractFrequentlyBoughtTogether(),
    editorialReviews: extractEditorialReviews(),
    extendedBookDetails: extractExtendedBookDetails(),
    customerQA: extractCustomerQA(),
    lookInsideAvailable: extractLookInsideAvailable(),
    seriesInfo: extractSeriesInfo(),
    kindleFeatures: extractKindleFeatures(),
  };
}

// Export for use in amazon-extractor.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    extractFrequentlyBoughtTogether,
    extractEditorialReviews,
    extractExtendedBookDetails,
    extractCustomerQA,
    extractLookInsideAvailable,
    extractSeriesInfo,
    extractKindleFeatures,
    extractEnrichmentData,
  };
}
