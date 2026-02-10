import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Home from "../page";

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

describe("Home Page", () => {
  it("renders the main heading", () => {
    render(<Home />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveTextContent("SelfPublisherForge");
  });

  it("renders the tagline", () => {
    render(<Home />);
    expect(
      screen.getByText("AI-powered self-publishing platform")
    ).toBeInTheDocument();
  });

  it("renders Sign In link pointing to /login", () => {
    render(<Home />);
    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toBeInTheDocument();
    expect(signInLink).toHaveAttribute("href", "/login");
  });

  it("renders Get Started link pointing to /register", () => {
    render(<Home />);
    const getStartedLink = screen.getByRole("link", { name: /get started/i });
    expect(getStartedLink).toBeInTheDocument();
    expect(getStartedLink).toHaveAttribute("href", "/register");
  });

  it("applies correct layout classes to main element", () => {
    render(<Home />);
    const main = screen.getByRole("main");
    expect(main).toHaveClass("flex", "min-h-screen", "flex-col", "items-center", "justify-center");
  });
});
