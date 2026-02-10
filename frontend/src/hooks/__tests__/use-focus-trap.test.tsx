import React, { useRef } from "react";
import { render, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useFocusTrap } from "@/hooks/use-focus-trap";

// ─── Helpers ────────────────────────────────────────────────────────────────

/**
 * Test harness component that wraps useFocusTrap with a configurable container.
 * Renders focusable elements inside a div so we can test Tab / Shift+Tab trapping.
 */
function FocusTrapHarness({
  active,
  onEscape,
  autoFocus = true,
  restoreFocus = true,
  children,
}: {
  active: boolean;
  onEscape?: () => void;
  autoFocus?: boolean;
  restoreFocus?: boolean;
  children?: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useFocusTrap(containerRef, { active, onEscape, autoFocus, restoreFocus });

  return (
    <div ref={containerRef} data-testid="trap-container">
      {children}
    </div>
  );
}

/**
 * Default content with three focusable buttons.
 */
function DefaultButtons() {
  return (
    <>
      <button data-testid="btn-first">First</button>
      <button data-testid="btn-second">Second</button>
      <button data-testid="btn-last">Last</button>
    </>
  );
}

// ─── Mock offsetParent ──────────────────────────────────────────────────────

// jsdom does not compute layout, so `offsetParent` is always `null`.
// The hook filters by `el.offsetParent !== null`, so we need to fake it.
beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetParent", {
    configurable: true,
    get() {
      return this.parentElement || document.body;
    },
  });
});

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("useFocusTrap", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("does not trap focus when active=false", () => {
    const outsideButton = document.createElement("button");
    outsideButton.textContent = "Outside";
    document.body.appendChild(outsideButton);
    outsideButton.focus();

    render(
      <FocusTrapHarness active={false} autoFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    // Focus should remain on the outside button
    expect(document.activeElement).toBe(outsideButton);

    // Tab keydown should not be intercepted — no preventDefault
    const tabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true,
    });
    const wasPrevented = !document.dispatchEvent(tabEvent);
    expect(wasPrevented).toBe(false);

    document.body.removeChild(outsideButton);
  });

  it("traps Tab at last element to first element", () => {
    render(
      <FocusTrapHarness active={true} autoFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    // Flush requestAnimationFrame
    act(() => {
      jest.runAllTimers();
    });

    const lastBtn = document.querySelector(
      '[data-testid="btn-last"]'
    ) as HTMLElement;
    const firstBtn = document.querySelector(
      '[data-testid="btn-first"]'
    ) as HTMLElement;

    // Focus the last button
    act(() => {
      lastBtn.focus();
    });
    expect(document.activeElement).toBe(lastBtn);

    // Simulate Tab keydown
    fireEvent.keyDown(document, { key: "Tab", shiftKey: false });

    // Focus should wrap to the first element
    expect(document.activeElement).toBe(firstBtn);
  });

  it("traps Shift+Tab at first element to last element", () => {
    render(
      <FocusTrapHarness active={true} autoFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    const firstBtn = document.querySelector(
      '[data-testid="btn-first"]'
    ) as HTMLElement;
    const lastBtn = document.querySelector(
      '[data-testid="btn-last"]'
    ) as HTMLElement;

    // Focus the first button
    act(() => {
      firstBtn.focus();
    });
    expect(document.activeElement).toBe(firstBtn);

    // Simulate Shift+Tab keydown
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });

    // Focus should wrap to the last element
    expect(document.activeElement).toBe(lastBtn);
  });

  it("calls onEscape when Escape pressed", () => {
    const onEscape = jest.fn();

    render(
      <FocusTrapHarness active={true} onEscape={onEscape}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onEscape).toHaveBeenCalledTimes(1);
  });

  it("restores focus on deactivation", () => {
    // Create an outside button and focus it before mounting the trap
    const outsideButton = document.createElement("button");
    outsideButton.textContent = "Outside";
    document.body.appendChild(outsideButton);
    outsideButton.focus();

    expect(document.activeElement).toBe(outsideButton);

    const { rerender } = render(
      <FocusTrapHarness active={true} restoreFocus={true}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    // Focus should have moved inside the trap
    const firstBtn = document.querySelector(
      '[data-testid="btn-first"]'
    ) as HTMLElement;
    expect(document.activeElement).toBe(firstBtn);

    // Deactivate the trap
    rerender(
      <FocusTrapHarness active={false} restoreFocus={true}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    // The hook uses setTimeout(0) to restore focus
    act(() => {
      jest.runAllTimers();
    });

    expect(document.activeElement).toBe(outsideButton);

    document.body.removeChild(outsideButton);
  });

  it("does not restore focus when restoreFocus=false", () => {
    const outsideButton = document.createElement("button");
    outsideButton.textContent = "Outside";
    document.body.appendChild(outsideButton);
    outsideButton.focus();

    const { rerender } = render(
      <FocusTrapHarness active={true} restoreFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    // Deactivate the trap
    rerender(
      <FocusTrapHarness active={false} restoreFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    // Focus should NOT be on the outside button
    expect(document.activeElement).not.toBe(outsideButton);

    document.body.removeChild(outsideButton);
  });

  it("handles container with no focusable elements", () => {
    render(
      <FocusTrapHarness active={true} autoFocus={true}>
        <span>No focusable elements here</span>
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    // The container itself should receive tabindex and focus
    const container = document.querySelector(
      '[data-testid="trap-container"]'
    ) as HTMLElement;
    expect(container).toHaveAttribute("tabindex", "-1");
    expect(document.activeElement).toBe(container);

    // Tab should be prevented (no focusable elements to cycle to)
    const tabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true,
    });
    const wasPrevented = !document.dispatchEvent(tabEvent);
    expect(wasPrevented).toBe(true);
  });

  it("finds dynamically added focusable elements", async () => {
    function DynamicHarness() {
      const [showExtra, setShowExtra] = React.useState(false);
      const containerRef = useRef<HTMLDivElement>(null);

      useFocusTrap(containerRef, { active: true, autoFocus: false });

      return (
        <div ref={containerRef} data-testid="trap-container-dynamic">
          <button data-testid="btn-static">Static</button>
          {showExtra && (
            <button data-testid="btn-dynamic">Dynamic</button>
          )}
          <button
            data-testid="btn-toggle"
            onClick={() => setShowExtra(true)}
          >
            Toggle
          </button>
        </div>
      );
    }

    render(<DynamicHarness />);

    act(() => {
      jest.runAllTimers();
    });

    // Initially only two buttons exist; focus the toggle (which is "last")
    const toggleBtn = document.querySelector(
      '[data-testid="btn-toggle"]'
    ) as HTMLElement;
    act(() => {
      toggleBtn.focus();
    });

    // Tab should wrap to the first static button
    fireEvent.keyDown(document, { key: "Tab", shiftKey: false });
    const staticBtn = document.querySelector(
      '[data-testid="btn-static"]'
    ) as HTMLElement;
    expect(document.activeElement).toBe(staticBtn);

    // Now add the dynamic button
    await act(async () => {
      fireEvent.click(toggleBtn);
    });

    act(() => {
      jest.runAllTimers();
    });

    // Focus the new dynamic button (which is now the middle element)
    // The toggle button is last; focus it and Tab should wrap to static
    act(() => {
      toggleBtn.focus();
    });

    fireEvent.keyDown(document, { key: "Tab", shiftKey: false });
    expect(document.activeElement).toBe(staticBtn);

    // Shift+Tab from static should wrap to toggle (the last focusable)
    act(() => {
      staticBtn.focus();
    });
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(toggleBtn);
  });

  it("auto-focuses the first focusable element when autoFocus=true", () => {
    render(
      <FocusTrapHarness active={true} autoFocus={true}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    const firstBtn = document.querySelector(
      '[data-testid="btn-first"]'
    ) as HTMLElement;
    expect(document.activeElement).toBe(firstBtn);
  });

  it("does not auto-focus when autoFocus=false", () => {
    const outsideButton = document.createElement("button");
    outsideButton.textContent = "Outside";
    document.body.appendChild(outsideButton);
    outsideButton.focus();

    render(
      <FocusTrapHarness active={true} autoFocus={false}>
        <DefaultButtons />
      </FocusTrapHarness>
    );

    act(() => {
      jest.runAllTimers();
    });

    // Focus should not have moved to the first button inside the trap
    const firstBtn = document.querySelector(
      '[data-testid="btn-first"]'
    ) as HTMLElement;
    expect(document.activeElement).not.toBe(firstBtn);

    document.body.removeChild(outsideButton);
  });
});
