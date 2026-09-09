/**
 * jest-axe ships no type declarations, so `import { axe } from "jest-axe"`
 * is an implicit any (TS7016) and `expect(...).toHaveNoViolations()` is
 * unknown on JestMatchers (TS2339).
 *
 * Declares only the surface the accessibility suites actually use.
 */
declare module "jest-axe" {
  export function axe(
    html: Element | string,
    options?: Record<string, unknown>
  ): Promise<unknown>;
  // Shaped for expect.extend(), which requires a matcher map.
  export const toHaveNoViolations: {
    toHaveNoViolations(received: unknown): {
      pass: boolean;
      message(): string;
    };
  };
  export function configureAxe(
    options?: Record<string, unknown>
  ): typeof axe;
}

declare namespace jest {
  interface Matchers<R> {
    toHaveNoViolations(): R;
  }
}
