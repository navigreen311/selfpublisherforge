import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { lazyLoad, lazyLoadSSR, lazyLoadNamed } from "../lazy";

// Mock next/dynamic
jest.mock("next/dynamic", () => {
  return (importFn: any, options?: any) => {
    const Component = React.lazy(() => {
      const promise = importFn();
      return promise;
    });

    return (props: any) => {
      const LoadingComponent = options?.loading;
      return (
        <React.Suspense fallback={LoadingComponent ? <LoadingComponent /> : <div>Loading...</div>}>
          <Component {...props} />
        </React.Suspense>
      );
    };
  };
});

// Test component
const TestComponent = ({ text }: { text: string }) => <div>{text}</div>;

describe("lazy loading utilities", () => {
  describe("lazyLoad", () => {
    it("loads component dynamically with default skeleton fallback", async () => {
      const LazyComponent = lazyLoad(() =>
        Promise.resolve({ default: TestComponent })
      );

      render(<LazyComponent text="Hello lazy loading!" />);

      // Should show skeleton while loading
      expect(document.querySelector(".animate-pulse")).toBeInTheDocument();

      // Should load the component
      await waitFor(() => {
        expect(screen.getByText("Hello lazy loading!")).toBeInTheDocument();
      });
    });

    it("loads component with custom fallback", async () => {
      const customFallback = <div>Custom loading...</div>;
      const LazyComponent = lazyLoad(
        () => Promise.resolve({ default: TestComponent }),
        customFallback
      );

      render(<LazyComponent text="Test content" />);

      // Should show custom fallback
      expect(screen.getByText("Custom loading...")).toBeInTheDocument();

      // Should load the component
      await waitFor(() => {
        expect(screen.getByText("Test content")).toBeInTheDocument();
      });
    });
  });

  describe("lazyLoadSSR", () => {
    it("loads component with SSR enabled", async () => {
      const LazyComponent = lazyLoadSSR(() =>
        Promise.resolve({ default: TestComponent })
      );

      render(<LazyComponent text="SSR test" />);

      await waitFor(() => {
        expect(screen.getByText("SSR test")).toBeInTheDocument();
      });
    });
  });

  describe("lazyLoadNamed", () => {
    it("loads named export from module", async () => {
      const LazyComponent = lazyLoadNamed(
        () => Promise.resolve({ TestComponent }),
        "TestComponent"
      );

      render(<LazyComponent text="Named export test" />);

      await waitFor(() => {
        expect(screen.getByText("Named export test")).toBeInTheDocument();
      });
    });

    it("loads named export with custom fallback", async () => {
      const customFallback = <div>Loading named export...</div>;
      const LazyComponent = lazyLoadNamed(
        () => Promise.resolve({ TestComponent }),
        "TestComponent",
        customFallback
      );

      render(<LazyComponent text="Test" />);

      // Should show custom fallback
      expect(screen.getByText("Loading named export...")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText("Test")).toBeInTheDocument();
      });
    });
  });
});
