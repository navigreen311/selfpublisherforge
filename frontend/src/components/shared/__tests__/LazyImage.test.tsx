import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LazyImage } from "../LazyImage";

// Mock Next.js Image component
jest.mock("next/image", () => ({
  __esModule: true,
  // Named so react-hooks/rules-of-hooks recognises it as a component
  // (an anonymous arrow assigned to `default` reads as a lowercase name).
  default: function MockNextImage(props: any) {
    // Simulate image loading
    React.useEffect(() => {
      if (props.onLoad) {
        setTimeout(() => props.onLoad(), 100);
      }
    }, [props.onLoad]);

    return (
      <img
        data-testid="next-image"
        src={props.src}
        alt={props.alt}
        width={props.width}
        height={props.height}
        className={props.className}
        style={props.style}
        loading={props.loading}
      />
    );
  },
}));

describe("LazyImage", () => {
  it("renders image with correct src and alt", () => {
    render(<LazyImage src="/test-image.jpg" alt="Test image" width={400} height={300} />);

    const image = screen.getByTestId("next-image");
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute("src", "/test-image.jpg");
    expect(image).toHaveAttribute("alt", "Test image");
  });

  it("renders with correct width and height", () => {
    render(<LazyImage src="/test.jpg" alt="Test" width={800} height={600} />);

    const image = screen.getByTestId("next-image");
    expect(image).toHaveAttribute("width", "800");
    expect(image).toHaveAttribute("height", "600");
  });

  it("applies custom className", () => {
    const { container } = render(
      <LazyImage
        src="/test.jpg"
        alt="Test"
        width={400}
        height={300}
        className="custom-image-class"
      />
    );

    const wrapper = container.querySelector(".custom-image-class");
    expect(wrapper).toBeInTheDocument();
  });

  it("uses lazy loading by default", () => {
    render(<LazyImage src="/test.jpg" alt="Test" width={400} height={300} />);

    const image = screen.getByTestId("next-image");
    expect(image).toHaveAttribute("loading", "lazy");
  });

  it("uses priority loading when specified", () => {
    render(
      <LazyImage src="/test.jpg" alt="Test" width={400} height={300} priority />
    );

    const image = screen.getByTestId("next-image");
    expect(image).not.toHaveAttribute("loading", "lazy");
  });

  it("calls onLoad callback when image loads", async () => {
    const onLoad = jest.fn();
    render(
      <LazyImage
        src="/test.jpg"
        alt="Test"
        width={400}
        height={300}
        onLoad={onLoad}
      />
    );

    await waitFor(
      () => {
        expect(onLoad).toHaveBeenCalledTimes(1);
      },
      { timeout: 200 }
    );
  });

  it("shows loading state initially", () => {
    const { container } = render(
      <LazyImage src="/test.jpg" alt="Test" width={400} height={300} />
    );

    const loadingIndicator = container.querySelector(".animate-pulse");
    expect(loadingIndicator).toBeInTheDocument();
  });

  it("applies correct object fit style", () => {
    render(
      <LazyImage
        src="/test.jpg"
        alt="Test"
        width={400}
        height={300}
        objectFit="contain"
      />
    );

    const image = screen.getByTestId("next-image");
    expect(image).toHaveStyle({ objectFit: "contain" });
  });

  it("uses fill layout when specified", () => {
    render(<LazyImage src="/test.jpg" alt="Test" fill />);

    const image = screen.getByTestId("next-image");
    expect(image).not.toHaveAttribute("width");
    expect(image).not.toHaveAttribute("height");
  });

  it("applies custom quality setting", () => {
    // Note: Next.js Image quality is not directly testable in jsdom,
    // but we can verify the component renders without errors
    render(
      <LazyImage
        src="/test.jpg"
        alt="Test"
        width={400}
        height={300}
        quality={90}
      />
    );

    expect(screen.getByTestId("next-image")).toBeInTheDocument();
  });
});
