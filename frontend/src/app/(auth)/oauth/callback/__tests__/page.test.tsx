import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
let mockSearchParamsMap: Record<string, string> = {};

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  useSearchParams: () => ({
    get: (key: string) => mockSearchParamsMap[key] || null,
  }),
}));

const mockHandleOAuthCallback = jest.fn();

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    handleOAuthCallback: mockHandleOAuthCallback,
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    checkAuth: jest.fn(),
    loginWithGoogle: jest.fn(),
    loginWithGitHub: jest.fn(),
  }),
}));

jest.mock("lucide-react", () => ({
  Loader2: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="loader-icon" {...props} />
  ),
}));

// Mock Radix UI Slot so that Button renders correctly
jest.mock("@radix-ui/react-slot", () => ({
  // @radix-ui/react-primitive calls createSlot() at module load, so a mock
  // without it throws before any test in the file runs.
  createSlot: () =>
    React.forwardRef(function MockSlot(
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLElement>
    ) {
      return React.isValidElement(children)
        ? React.cloneElement(children, { ...props, ref } as Record<string, unknown>)
        : React.createElement("span", { ref, ...props }, children as React.ReactNode);
    }),
  createSlottable: () =>
    function MockSlottable({ children }: { children?: React.ReactNode }) {
      return children as React.ReactElement;
    },
  Slot: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => {
      if (React.isValidElement(children)) {
        return React.cloneElement(children, {
          ...props,
          ref,
        } as Record<string, unknown>);
      }
      return (
        <div ref={ref} {...props}>
          {children}
        </div>
      );
    }
  ),
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import OAuthCallbackPage from "../page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("OAuthCallbackPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParamsMap = {};
    mockHandleOAuthCallback.mockResolvedValue(undefined);
  });

  it("shows loading state with spinner and 'Signing you in' text", () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    render(<OAuthCallbackPage />);

    expect(screen.getByText("Signing you in")).toBeInTheDocument();
    expect(
      screen.getByText("Please wait while we complete authentication...")
    ).toBeInTheDocument();
    expect(screen.getByTestId("loader-icon")).toBeInTheDocument();
  });

  it("shows error when no code param is present", async () => {
    mockSearchParamsMap = { provider: "google" };
    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(
        screen.getByText("No authorization code received. Please try again.")
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Authentication failed")).toBeInTheDocument();
  });

  it("shows error when no provider param is present", async () => {
    mockSearchParamsMap = { code: "abc123" };
    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Could not determine the OAuth provider. Please try again."
        )
      ).toBeInTheDocument();
    });
  });

  it("calls handleOAuthCallback with provider and code", async () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(mockHandleOAuthCallback).toHaveBeenCalledWith("google", "abc123");
    });
  });

  it("uses state param as fallback for provider", async () => {
    mockSearchParamsMap = { code: "abc123", state: "github" };
    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(mockHandleOAuthCallback).toHaveBeenCalledWith("github", "abc123");
    });
  });

  it("shows error state when callback fails", async () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    mockHandleOAuthCallback.mockRejectedValue(
      new Error("Invalid authorization code")
    );

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Invalid authorization code")
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Authentication failed")).toBeInTheDocument();
  });

  it("shows generic error message for non-Error rejections", async () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    mockHandleOAuthCallback.mockRejectedValue("unexpected string error");

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Authentication failed. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it('renders "Back to login" button that navigates to /login', async () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    mockHandleOAuthCallback.mockRejectedValue(new Error("Auth failed"));

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(screen.getByText("Authentication failed")).toBeInTheDocument();
    });

    const backButton = screen.getByRole("button", { name: /back to login/i });
    expect(backButton).toBeInTheDocument();

    await userEvent.click(backButton);
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("renders in a Card layout", () => {
    mockSearchParamsMap = { code: "abc123", provider: "google" };
    render(<OAuthCallbackPage />);

    // The card should have the max-w-md class
    const card = document.querySelector(".max-w-md");
    expect(card).toBeInTheDocument();
  });
});
