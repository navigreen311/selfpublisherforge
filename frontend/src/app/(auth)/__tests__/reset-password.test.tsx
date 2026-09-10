import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
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

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

const mockPost = jest.fn();
jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: (...args: unknown[]) => mockPost(...args),
    put: jest.fn().mockResolvedValue({ data: {} }),
    patch: jest.fn().mockResolvedValue({ data: {} }),
    delete: jest.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  },
}));

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Eye: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="eye-icon" {...props} />
  ),
  EyeOff: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="eye-off-icon" {...props} />
  ),
  Check: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="check-icon" {...props} />
  ),
}));

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

import ResetPasswordPage from "../reset-password/page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("ResetPasswordPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParamsMap = { token: "valid-reset-token-123" };
    mockPost.mockResolvedValue({ data: {} });
  });

  it("renders the password reset form when token is present", () => {
    render(<ResetPasswordPage />);

    expect(screen.getByText("Reset your password")).toBeInTheDocument();
    expect(
      screen.getByText("Enter your new password below.")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Enter your new password")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Confirm your new password")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeInTheDocument();
  });

  it("shows invalid token message when no token is provided", () => {
    mockSearchParamsMap = {};
    render(<ResetPasswordPage />);

    expect(screen.getByText("Invalid reset link")).toBeInTheDocument();
    expect(
      screen.getByText(/this password reset link is invalid or has expired/i)
    ).toBeInTheDocument();
  });

  it("has a link to request a new reset link when token is missing", () => {
    mockSearchParamsMap = {};
    render(<ResetPasswordPage />);

    const requestLink = screen.getByRole("link", {
      name: /request new reset link/i,
    });
    expect(requestLink).toBeInTheDocument();
    expect(requestLink).toHaveAttribute("href", "/forgot-password");
  });

  it("displays password validation checks when typing", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ab"
    );

    expect(screen.getByText("8+ characters")).toBeInTheDocument();
    expect(screen.getByText("Uppercase letter")).toBeInTheDocument();
    expect(screen.getByText("Lowercase letter")).toBeInTheDocument();
    expect(screen.getByText("Number")).toBeInTheDocument();
  });

  it("shows passwords do not match message", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "DifferentPass1"
    );

    expect(
      screen.getByText("Passwords do not match.")
    ).toBeInTheDocument();
  });

  it("does not show mismatch message when passwords match", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );

    expect(
      screen.queryByText("Passwords do not match.")
    ).not.toBeInTheDocument();
  });

  it("disables submit button when password is invalid", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "weak"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "weak"
    );

    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeDisabled();
  });

  it("disables submit button when passwords do not match", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass2"
    );

    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeDisabled();
  });

  it("enables submit button when password is valid and passwords match", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );

    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeEnabled();
  });

  it("shows success state after successful password reset", async () => {
    const user = userEvent.setup();
    mockPost.mockResolvedValue({ data: {} });
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText("Password reset successful")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/your password has been reset successfully/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /sign in now/i })
    ).toBeInTheDocument();
  });

  it("calls the reset API with token and new password", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/reset-password", {
        token: "valid-reset-token-123",
        new_password: "ValidPass1",
      });
    });
  });

  it("shows error message when API call fails", async () => {
    const user = userEvent.setup();
    mockPost.mockRejectedValue(new Error("Token has expired"));
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(screen.getByText("Token has expired")).toBeInTheDocument();
    });
  });

  it("shows generic error for non-Error API failures", async () => {
    const user = userEvent.setup();
    mockPost.mockRejectedValue("unexpected");
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          "Failed to reset password. The link may have expired. Please request a new one."
        )
      ).toBeInTheDocument();
    });
  });

  it("has a link back to sign in", () => {
    render(<ResetPasswordPage />);

    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toBeInTheDocument();
    expect(signInLink).toHaveAttribute("href", "/login");
  });

  it("disables the submit button while loading", async () => {
    const user = userEvent.setup();
    // Make the API call hang
    mockPost.mockReturnValue(new Promise(() => {}));
    render(<ResetPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("Enter your new password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Confirm your new password"),
      "ValidPass1"
    );
    await user.click(
      screen.getByRole("button", { name: /reset password/i })
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /resetting password/i })
      ).toBeDisabled();
    });
  });

  it("toggles password visibility for new password field", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    const passwordInput = screen.getByPlaceholderText(
      "Enter your new password"
    );
    expect(passwordInput).toHaveAttribute("type", "password");

    // There are two eye icons (one per password field) — get the first one
    const eyeIcons = screen.getAllByTestId("eye-icon");
    const firstToggle = eyeIcons[0].closest("button")!;
    await user.click(firstToggle);

    expect(passwordInput).toHaveAttribute("type", "text");
  });

  it("toggles password visibility for confirm password field", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />);

    const confirmInput = screen.getByPlaceholderText(
      "Confirm your new password"
    );
    expect(confirmInput).toHaveAttribute("type", "password");

    const eyeIcons = screen.getAllByTestId("eye-icon");
    const secondToggle = eyeIcons[1].closest("button")!;
    await user.click(secondToggle);

    expect(confirmInput).toHaveAttribute("type", "text");
  });
});
