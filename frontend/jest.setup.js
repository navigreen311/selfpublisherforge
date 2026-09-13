import "@testing-library/jest-dom";

/**
 * jsdom gaps that Radix and the shared components trip over.
 *
 * Radix's menu, select, dialog and popover primitives call the Pointer Capture
 * API and `scrollIntoView` while opening. jsdom implements neither, so the
 * click threw internally and the trigger stayed `data-state="closed"` — every
 * assertion about a dropdown's contents then failed with "Unable to find".
 * Observers are missing for the same reason and are needed by InfiniteScroll
 * and the responsive layout components.
 */

if (!window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (!window.IntersectionObserver) {
  window.IntersectionObserver = class IntersectionObserver {
    constructor(callback) {
      this.callback = callback;
    }
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  };
}

if (!window.matchMedia) {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = function scrollIntoView() {};
}

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = function hasPointerCapture() {
    return false;
  };
  Element.prototype.setPointerCapture = function setPointerCapture() {};
  Element.prototype.releasePointerCapture = function releasePointerCapture() {};
}
