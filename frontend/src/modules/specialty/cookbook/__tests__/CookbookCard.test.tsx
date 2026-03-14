import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CookbookCard } from "../components/CookbookCard";
import type { Cookbook } from "@/modules/specialty/types/cookbook";

jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string; [key: string]: unknown }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock("lucide-react", () => ({
  UtensilsCrossed: (props: React.SVGAttributes<SVGElement>) => <svg data-testid="utensils-icon" {...props} />,
  Image: (props: React.SVGAttributes<SVGElement>) => <svg data-testid="image-icon" {...props} />,
}));

const mockCookbook: Cookbook = {
  id: "test-cookbook-1", org_id: "org-1", title: "Italian Kitchen", author: "Chef Test",
  cookbook_type: "international", cuisine: "Italian", chapter_organization: "by_course",
  recipe_layout: "classic", illustration_method: "ai_generated", interior_type: "full_color",
  page_count: 120, trim_size: "8x10", include_nutrition: true, include_meal_plans: false,
  include_shopping_lists: false, include_index: true, include_conversion_charts: true,
  dietary_tags: [], status: "in-progress", qa_score: 72,
  created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z",
};

describe("CookbookCard", () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it("renders cookbook title", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("Italian Kitchen")).toBeInTheDocument(); });
  it("shows type badge", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("International")).toBeInTheDocument(); });
  it("shows page count", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("120p")).toBeInTheDocument(); });
  it("shows status badge", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("in-progress")).toBeInTheDocument(); });
  it("links to cookbook detail page", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByRole("link")).toHaveAttribute("href", "/specialty/cookbook-books/test-cookbook-1"); });
  it("renders QA score", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("72")).toBeInTheDocument(); });
  it("shows placeholder when no cover", () => { render(<CookbookCard cookbook={mockCookbook} />); expect(screen.getByText("No Cover")).toBeInTheDocument(); });
  it("shows cover image when available", () => { render(<CookbookCard cookbook={{ ...mockCookbook, cover_image_url: "https://example.com/cover.jpg" }} />); expect(screen.getByRole("img")).toHaveAttribute("src", "https://example.com/cover.jpg"); });
});
