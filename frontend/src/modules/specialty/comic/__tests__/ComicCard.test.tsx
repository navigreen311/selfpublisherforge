import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ComicCard } from "../components/ComicCard";
import type { Comic } from "../hooks";

jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string; [key: string]: unknown }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  BookOpen: (props: React.SVGAttributes<SVGElement>) => <svg data-testid="book-open-icon" {...props} />,
  Image: (props: React.SVGAttributes<SVGElement>) => <svg data-testid="image-icon" {...props} />,
}));

const mockComic: Comic = {
  id: "test-comic-1", org_id: "org-1", title: "Test Comic Book", format: "graphic_novel",
  art_style: "american_classic", color_mode: "full_color", ink_style: "clean", pacing: "balanced",
  target_audience: "all_ages", page_count: 24, trim_size: "6.625x10.25", border_style: "solid",
  gutter_style: "standard", status: "draft", qa_score: 85,
  created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z",
};

describe("ComicCard", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it("renders comic title", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("Test Comic Book")).toBeInTheDocument(); });
  it("shows format badge", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("Graphic Novel")).toBeInTheDocument(); });
  it("shows page count", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("24p")).toBeInTheDocument(); });
  it("shows status badge", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("draft")).toBeInTheDocument(); });
  it("links to comic detail page", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByRole("link")).toHaveAttribute("href", "/specialty/comic-books/test-comic-1"); });
  it("shows cover image when available", () => { render(<ComicCard comic={{ ...mockComic, cover_image_url: "https://example.com/cover.jpg" }} />); expect(screen.getByRole("img")).toHaveAttribute("src", "https://example.com/cover.jpg"); });
  it("shows placeholder when no cover", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("No Cover")).toBeInTheDocument(); });
  it("renders QA score", () => { render(<ComicCard comic={mockComic} />); expect(screen.getByText("85")).toBeInTheDocument(); });
  it("renders zero QA score when undefined", () => { render(<ComicCard comic={{ ...mockComic, qa_score: undefined }} />); expect(screen.getByText("0")).toBeInTheDocument(); });
});
