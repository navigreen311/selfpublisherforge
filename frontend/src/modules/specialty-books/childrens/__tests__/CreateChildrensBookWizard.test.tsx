import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

// Mock hooks
const mockCreate = jest.fn();
jest.mock("../hooks", () => ({
  useCreateChildrensBook: () => ({ mutate: mockCreate, isPending: false }),
}));

import { CreateChildrensBookWizard } from "../components/CreateChildrensBookWizard";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("CreateChildrensBookWizard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the dialog when open", () => {
    render(
      <CreateChildrensBookWizard open={true} onOpenChange={jest.fn()} />,
      { wrapper },
    );
    expect(screen.getByText("Create Children\u2019s Book")).toBeInTheDocument();
    expect(screen.getByText(/title/i)).toBeInTheDocument();
  });

  it("does not render content when closed", () => {
    render(
      <CreateChildrensBookWizard open={false} onOpenChange={jest.fn()} />,
      { wrapper },
    );
    expect(screen.queryByText("Create Children\u2019s Book")).not.toBeInTheDocument();
  });

  it("disables Next when title and author are empty", () => {
    render(
      <CreateChildrensBookWizard open={true} onOpenChange={jest.fn()} />,
      { wrapper },
    );
    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).toBeDisabled();
  });

  it("enables Next when title and author are filled", () => {
    render(
      <CreateChildrensBookWizard open={true} onOpenChange={jest.fn()} />,
      { wrapper },
    );
    const titleInput = screen.getByPlaceholderText("My Amazing Story");
    const authorInput = screen.getByPlaceholderText("Your name or pen name");

    fireEvent.change(titleInput, { target: { value: "Test Book" } });
    fireEvent.change(authorInput, { target: { value: "Author Name" } });

    const nextBtn = screen.getByRole("button", { name: /next/i });
    expect(nextBtn).toBeEnabled();
  });
});
