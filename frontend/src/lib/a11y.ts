/**
 * Accessibility utility helpers for WCAG 2.1 AA compliance
 */

/**
 * Announces a message to screen readers using aria-live
 * Creates a temporary element that is removed after announcement
 *
 * @param message - The message to announce
 * @param priority - "polite" (default) or "assertive"
 *
 * @example
 * ```ts
 * announceToScreenReader("Data loaded successfully");
 * announceToScreenReader("Error: Please try again", "assertive");
 * ```
 */
export function announceToScreenReader(
  message: string,
  priority: "polite" | "assertive" = "polite"
): void {
  if (typeof window === "undefined") return;

  const announcement = document.createElement("div");
  announcement.setAttribute("role", "status");
  announcement.setAttribute("aria-live", priority);
  announcement.setAttribute("aria-atomic", "true");
  announcement.className = "sr-only";
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement is complete
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * Generates a unique ID for associating labels with form controls
 *
 * @param prefix - Optional prefix for the ID
 * @returns A unique ID string
 *
 * @example
 * ```tsx
 * const id = generateA11yId("input");
 * <label htmlFor={id}>Name</label>
 * <input id={id} />
 * ```
 */
export function generateA11yId(prefix = "a11y"): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Checks if an element has sufficient color contrast ratio
 * This is a simplified check - use automated tools for comprehensive testing
 *
 * @param foreground - Foreground color (hex)
 * @param background - Background color (hex)
 * @param isLargeText - Whether the text is large (18pt+ or 14pt+ bold)
 * @returns Whether contrast meets WCAG AA standards
 */
export function hasValidContrast(
  foreground: string,
  background: string,
  isLargeText = false
): boolean {
  const ratio = calculateContrastRatio(foreground, background);
  const threshold = isLargeText ? 3 : 4.5;
  return ratio >= threshold;
}

/**
 * Calculates the contrast ratio between two colors
 *
 * @param color1 - First color (hex)
 * @param color2 - Second color (hex)
 * @returns Contrast ratio (1-21)
 */
function calculateContrastRatio(color1: string, color2: string): number {
  const l1 = getRelativeLuminance(color1);
  const l2 = getRelativeLuminance(color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Gets the relative luminance of a color
 *
 * @param hex - Hex color code
 * @returns Relative luminance (0-1)
 */
function getRelativeLuminance(hex: string): number {
  const rgb = hexToRgb(hex);
  const [r, g, b] = rgb.map((val) => {
    const normalized = val / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Converts hex color to RGB array
 *
 * @param hex - Hex color code
 * @returns RGB array [r, g, b]
 */
function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16),
      ]
    : [0, 0, 0];
}

/**
 * Creates a focus trap for modals/dialogs
 * Returns a cleanup function to remove the trap
 *
 * @param element - The element to trap focus within
 * @returns Cleanup function
 *
 * @example
 * ```tsx
 * useEffect(() => {
 *   const cleanup = createFocusTrap(dialogRef.current);
 *   return cleanup;
 * }, []);
 * ```
 */
export function createFocusTrap(element: HTMLElement | null): () => void {
  if (!element) return () => {};

  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(", ");

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== "Tab") return;

    const focusableElements = Array.from(
      element.querySelectorAll<HTMLElement>(focusableSelectors)
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  };

  element.addEventListener("keydown", handleKeyDown);

  // Focus first element
  const firstFocusable = element.querySelector<HTMLElement>(focusableSelectors);
  firstFocusable?.focus();

  return () => {
    element.removeEventListener("keydown", handleKeyDown);
  };
}

/**
 * Gets accessible label text from an element
 * Checks aria-label, aria-labelledby, and associated label elements
 *
 * @param element - The element to get the label from
 * @returns The accessible label text or null
 */
export function getAccessibleLabel(element: HTMLElement): string | null {
  // Check aria-label
  const ariaLabel = element.getAttribute("aria-label");
  if (ariaLabel) return ariaLabel;

  // Check aria-labelledby
  const labelledBy = element.getAttribute("aria-labelledby");
  if (labelledBy) {
    const labelElement = document.getElementById(labelledBy);
    if (labelElement) return labelElement.textContent;
  }

  // Check for associated label (for form inputs)
  if (element instanceof HTMLInputElement && element.id) {
    const label = document.querySelector(`label[for="${element.id}"]`);
    if (label) return label.textContent;
  }

  return null;
}

/**
 * Checks if keyboard navigation is currently being used
 * Useful for showing/hiding focus indicators
 *
 * @returns Whether keyboard navigation is active
 */
export function isKeyboardNavigation(): boolean {
  if (typeof window === "undefined") return false;

  // Check if last interaction was keyboard
  return document.body.classList.contains("using-keyboard");
}

/**
 * Sets up keyboard navigation detection
 * Adds/removes "using-keyboard" class on body
 * Call this once in your app initialization
 */
export function setupKeyboardNavigationDetection(): () => void {
  if (typeof window === "undefined") return () => {};

  const handleMouseDown = () => {
    document.body.classList.remove("using-keyboard");
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Tab") {
      document.body.classList.add("using-keyboard");
    }
  };

  window.addEventListener("mousedown", handleMouseDown);
  window.addEventListener("keydown", handleKeyDown);

  return () => {
    window.removeEventListener("mousedown", handleMouseDown);
    window.removeEventListener("keydown", handleKeyDown);
  };
}
