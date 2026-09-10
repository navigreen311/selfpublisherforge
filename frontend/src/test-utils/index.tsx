/**
 * Testing-library re-export with the providers a rendered page actually needs.
 *
 * Components that call a react-query hook throw "No QueryClient set" when
 * rendered bare, which kills the suite before any assertion. Import `render`
 * from here instead of from `@testing-library/react` and it arrives wrapped.
 *
 * A fresh QueryClient per render keeps suites isolated, and retries are off so
 * a failing query surfaces immediately rather than after three backoffs.
 */

import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render as rtlRender, type RenderOptions } from "@testing-library/react";

export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function AllProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(createTestQueryClient);
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

function render(ui: React.ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return rtlRender(ui, { wrapper: AllProviders, ...options });
}

export * from "@testing-library/react";
export { render };
