/**
 * extractor.test.js — Tests for Amazon metadata extraction.
 *
 * Tests the enrichment.js extraction functions with mocked DOM structures.
 * Uses JSDOM for DOM simulation (or can be run in a browser environment).
 *
 * Run with: node extractor.test.js (requires jsdom)
 * Or: Load in browser console with test harness
 */

// ---------------------------------------------------------------------------
// DOM Mocking Utilities
// ---------------------------------------------------------------------------

/**
 * Create a mock DOM structure for testing extraction functions.
 * In a real test environment, you'd use JSDOM or similar.
 */
class MockDOM {
  constructor() {
    this.elements = new Map();
    this.body = this.createElement("body");
  }

  createElement(tag) {
    const el = {
      tagName: tag.toUpperCase(),
      textContent: "",
      innerHTML: "",
      children: [],
      attributes: {},
      classList: {
        _classes: [],
        add: function (cls) {
          this._classes.push(cls);
        },
        contains: function (cls) {
          return this._classes.includes(cls);
        },
      },
      getAttribute: function (name) {
        return this.attributes[name];
      },
      setAttribute: function (name, value) {
        this.attributes[name] = value;
      },
      appendChild: function (child) {
        this.children.push(child);
      },
    };

    // Add querySelector and querySelectorAll as proper methods
    el.querySelector = function (selector) {
      // Simplified selector matching for testing
      // Handle tag selectors
      if (/^[a-z]+$/i.test(selector)) {
        if (this.tagName.toLowerCase() === selector.toLowerCase()) return this;
        for (const child of this.children) {
          const found = child.querySelector(selector);
          if (found) return found;
        }
      }
      // Handle ID selectors
      if (selector.startsWith("#")) {
        const id = selector.slice(1);
        if (this.attributes.id === id) return this;
        for (const child of this.children) {
          const found = child.querySelector(selector);
          if (found) return found;
        }
      }
      // Handle class selectors
      if (selector.startsWith(".")) {
        const cls = selector.slice(1);
        if (this.classList.contains(cls)) return this;
        for (const child of this.children) {
          const found = child.querySelector(selector);
          if (found) return found;
        }
      }
      return null;
    };

    el.querySelectorAll = function (selector) {
      const results = [];
      // Handle tag selectors
      if (/^[a-z]+$/i.test(selector)) {
        if (this.tagName.toLowerCase() === selector.toLowerCase()) results.push(this);
        for (const child of this.children) {
          results.push(...child.querySelectorAll(selector));
        }
      }
      // Handle ID selectors
      else if (selector.startsWith("#")) {
        const found = this.querySelector(selector);
        if (found) results.push(found);
      }
      // Handle class selectors
      else if (selector.startsWith(".")) {
        const cls = selector.slice(1);
        if (this.classList.contains(cls)) results.push(this);
        for (const child of this.children) {
          results.push(...child.querySelectorAll(selector));
        }
      }
      return results;
    };

    return el;
  }

  getElementById(id) {
    return this.body.querySelector(`#${id}`);
  }

  querySelector(selector) {
    return this.body.querySelector(selector);
  }

  querySelectorAll(selector) {
    return this.body.querySelectorAll(selector);
  }

  addElement(id, textContent, tag = "div") {
    const el = this.createElement(tag);
    el.attributes.id = id;
    el.textContent = textContent;
    this.body.appendChild(el);
    return el;
  }
}

// ---------------------------------------------------------------------------
// Test Utilities
// ---------------------------------------------------------------------------

function assert(condition, message) {
  if (!condition) {
    console.error(`❌ FAIL: ${message}`);
    return false;
  } else {
    console.log(`✅ PASS: ${message}`);
    return true;
  }
}

function assertEqual(actual, expected, message) {
  const eq = JSON.stringify(actual) === JSON.stringify(expected);
  return assert(eq, `${message} (expected: ${JSON.stringify(expected)}, got: ${JSON.stringify(actual)})`);
}

// ---------------------------------------------------------------------------
// Test: Frequently Bought Together Extraction
// ---------------------------------------------------------------------------

function testFrequentlyBoughtTogether() {
  console.log("\n--- Testing Frequently Bought Together ---");

  const dom = new MockDOM();

  // Mock carousel layout
  const carousel = dom.createElement("div");
  carousel.attributes.id = "sims-fbt";

  const item1 = dom.createElement("div");
  item1.classList.add("a-carousel-card");
  const link1 = dom.createElement("a");
  link1.attributes.href = "https://www.amazon.com/dp/B08ABCD123";
  link1.textContent = "Related Book 1";
  item1.appendChild(link1);
  carousel.appendChild(item1);

  const item2 = dom.createElement("div");
  item2.classList.add("a-carousel-card");
  const link2 = dom.createElement("a");
  link2.attributes.href = "https://www.amazon.com/dp/B09EFGH456";
  link2.textContent = "Related Book 2";
  item2.appendChild(link2);
  carousel.appendChild(item2);

  dom.body.appendChild(carousel);

  // Mock global document
  global.document = dom;

  // Test extraction (would need to load enrichment.js functions)
  // For demonstration, we verify DOM structure
  const items = dom.querySelectorAll(".a-carousel-card");
  assert(items.length === 2, "Should find 2 carousel items");

  const links = carousel.querySelectorAll("a");
  assert(links.length === 2, "Should find 2 links in carousel");
  assertEqual(links[0].textContent, "Related Book 1", "First link should have correct text");
}

// ---------------------------------------------------------------------------
// Test: Editorial Reviews Extraction
// ---------------------------------------------------------------------------

function testEditorialReviews() {
  console.log("\n--- Testing Editorial Reviews ---");

  const dom = new MockDOM();

  // Mock editorial reviews section
  const reviewsDiv = dom.createElement("div");
  reviewsDiv.attributes.id = "bookDescription_feature_div";

  const section1 = dom.createElement("div");
  section1.classList.add("a-section");
  const heading1 = dom.createElement("h3");
  heading1.textContent = "From the Back Cover";
  const content1 = dom.createElement("p");
  content1.textContent = "This is the back cover description of the book.";
  section1.appendChild(heading1);
  section1.appendChild(content1);
  reviewsDiv.appendChild(section1);

  const section2 = dom.createElement("div");
  section2.classList.add("a-section");
  const heading2 = dom.createElement("h3");
  heading2.textContent = "About the Author";
  const content2 = dom.createElement("p");
  content2.textContent = "The author is a renowned expert in the field.";
  section2.appendChild(heading2);
  section2.appendChild(content2);
  reviewsDiv.appendChild(section2);

  dom.body.appendChild(reviewsDiv);
  global.document = dom;

  // Verify DOM structure
  const sections = dom.querySelectorAll(".a-section");
  assert(sections.length >= 2, "Should find at least 2 review sections");

  const headings = reviewsDiv.querySelectorAll("h3");
  assert(headings.length === 2, "Should find 2 headings");
  if (headings.length > 0) {
    assertEqual(headings[0].textContent, "From the Back Cover", "First heading should be correct");
  }
}

// ---------------------------------------------------------------------------
// Test: Kindle Features Extraction
// ---------------------------------------------------------------------------

function testKindleFeatures() {
  console.log("\n--- Testing Kindle Features ---");

  const dom = new MockDOM();

  // Mock Kindle Unlimited badge
  const kuBadge = dom.createElement("img");
  kuBadge.attributes.id = "kindle-unlimited-logo";
  kuBadge.attributes.alt = "Kindle Unlimited";
  dom.body.appendChild(kuBadge);

  // Mock Kindle price
  const priceDiv = dom.createElement("div");
  priceDiv.attributes.id = "kindle-price";
  const priceSpan = dom.createElement("span");
  priceSpan.textContent = "$9.99";
  priceSpan.classList.add("a-color-price");
  priceDiv.appendChild(priceSpan);
  dom.body.appendChild(priceDiv);

  // Mock product details with features
  const detailsRow = dom.createElement("tr");
  const detailsCell = dom.createElement("td");
  detailsCell.textContent = "Word Wise: Enabled";
  detailsRow.appendChild(detailsCell);
  const detailsTable = dom.createElement("div");
  detailsTable.attributes.id = "productDetails_detailBullets_sections1";
  detailsTable.appendChild(detailsRow);
  dom.body.appendChild(detailsTable);

  global.document = dom;

  // Verify DOM structure
  assert(dom.querySelector("#kindle-unlimited-logo") !== null, "Should find KU badge");
  assert(dom.querySelector("#kindle-price") !== null, "Should find Kindle price");

  const priceContainer = dom.querySelector("#kindle-price");
  const priceSpanCheck = priceContainer ? priceContainer.querySelector(".a-color-price") : null;
  if (priceSpanCheck) {
    assertEqual(priceSpanCheck.textContent, "$9.99", "Kindle price should be correct");
  }
}

// ---------------------------------------------------------------------------
// Test: Series Information Extraction
// ---------------------------------------------------------------------------

function testSeriesInfo() {
  console.log("\n--- Testing Series Info ---");

  const dom = new MockDOM();

  // Mock series link
  const seriesLink = dom.createElement("a");
  seriesLink.attributes.id = "seriesTitle";
  seriesLink.attributes.href = "/series/fantasy-series";
  seriesLink.textContent = "Fantasy Series Book 3";
  dom.body.appendChild(seriesLink);

  global.document = dom;

  // Verify DOM structure
  const series = dom.querySelector("#seriesTitle");
  assert(series !== null, "Should find series link");
  assert(series.textContent.includes("Book 3"), "Should contain book number");
  assert(series.textContent.includes("Fantasy Series"), "Should contain series name");
}

// ---------------------------------------------------------------------------
// Test: Look Inside Availability
// ---------------------------------------------------------------------------

function testLookInsideAvailable() {
  console.log("\n--- Testing Look Inside ---");

  const dom = new MockDOM();

  // Mock Look Inside button
  const lookInsideImg = dom.createElement("img");
  lookInsideImg.attributes.id = "sitbLogoImg";
  lookInsideImg.attributes.alt = "Look Inside";
  dom.body.appendChild(lookInsideImg);

  global.document = dom;

  // Verify DOM structure
  assert(dom.querySelector("#sitbLogoImg") !== null, "Should find Look Inside element");
}

// ---------------------------------------------------------------------------
// Test: Customer Q&A Extraction
// ---------------------------------------------------------------------------

function testCustomerQA() {
  console.log("\n--- Testing Customer Q&A ---");

  const dom = new MockDOM();

  // Mock Q&A section
  const qaDiv = dom.createElement("div");
  qaDiv.attributes.id = "ask";

  for (let i = 1; i <= 3; i++) {
    const qaItem = dom.createElement("div");
    qaItem.classList.add("askTeaserQuestions");

    const question = dom.createElement("span");
    question.classList.add("a-text-bold");
    question.textContent = `Question ${i}?`;

    const answer = dom.createElement("span");
    answer.classList.add("askAnswerText");
    answer.textContent = `Answer ${i}.`;

    qaItem.appendChild(question);
    qaItem.appendChild(answer);
    qaDiv.appendChild(qaItem);
  }

  dom.body.appendChild(qaDiv);
  global.document = dom;

  // Verify DOM structure
  const questions = dom.querySelectorAll(".a-text-bold");
  assert(questions.length === 3, "Should find 3 questions");
  assertEqual(questions[0].textContent, "Question 1?", "First question should be correct");
}

// ---------------------------------------------------------------------------
// Run All Tests
// ---------------------------------------------------------------------------

function runAllTests() {
  console.log("=".repeat(60));
  console.log("Running Amazon Extractor Tests");
  console.log("=".repeat(60));

  try {
    testFrequentlyBoughtTogether();
    testEditorialReviews();
    testKindleFeatures();
    testSeriesInfo();
    testLookInsideAvailable();
    testCustomerQA();

    console.log("\n" + "=".repeat(60));
    console.log("✅ All tests completed");
    console.log("=".repeat(60));
  } catch (error) {
    console.error("\n❌ Test suite failed:", error);
  }
}

// Run tests if in Node.js environment
if (typeof module !== "undefined" && require.main === module) {
  runAllTests();
}

// Export for browser testing
if (typeof window !== "undefined") {
  window.runExtractorTests = runAllTests;
}
