import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

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

jest.mock("lucide-react", () => ({
  // Spread the real module first: these factories list only the icons the test
  // asserts on, and any icon used deeper in the tree (dialog.tsx's X, for one)
  // arrived as undefined and crashed the render.
  ...jest.requireActual("lucide-react"),
  Mail: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="mail-icon" {...props} />
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

// ─── Import after mocks ─────────────────────────────────────────────────────

import ForgotPasswordPage from "../forgot-password/page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPost.mockResolvedValue({ data: {} });
  });

  it("renders the email input form", () => {
    render(<ForgotPasswordPage />);

    expect(
      screen.getByText("Forgot your password?")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("you@example.com")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send reset link/i })
    ).toBeInTheDocument();
  });

  it("renders a description explaining the form purpose", () => {
    render(<ForgotPasswordPage />);

    expect(
      screen.getByText(/enter your email address and we/i)
    ).toBeInTheDocument();
  });

  it("validates email format via HTML5 required attribute", () => {
    render(<ForgotPasswordPage />);

    const emailInput = screen.getByPlaceholderText("you@example.com");
    expect(emailInput).toBeRequired();
    expect(emailInput).toHaveAttribute("type", "email");
  });

  it("shows success message after successful submission", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/auth/forgot-password",
      { email: "test@example.com" }
    );
  });

  it("shows success even when API errors (prevents email enumeration)", async () => {
    const user = userEvent.setup();
    mockPost.mockRejectedValue(new Error("Not Found"));
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "nonexistent@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });
  });

  it("has link back to login from the initial form", () => {
    render(<ForgotPasswordPage />);

    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toBeInTheDocument();
    expect(signInLink).toHaveAttribute("href", "/login");
  });

  it("has link back to sign in from the success screen", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });

    const backLink = screen.getByRole("link", { name: /back to sign in/i });
    expect(backLink).toBeInTheDocument();
    expect(backLink).toHaveAttribute("href", "/login");
  });

  it("displays the submitted email in the success message", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "myemail@domain.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByText("myemail@domain.com")).toBeInTheDocument();
    });
  });

  it("allows retrying after viewing the success message", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });

    // Click "Try again" to go back to the form
    const tryAgainButton = screen.getByRole("button", { name: /try again/i });
    await user.click(tryAgainButton);

    // Should be back on the form
    expect(
      screen.getByPlaceholderText("you@example.com")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send reset link/i })
    ).toBeInTheDocument();
  });

  it("disables the submit button while loading", async () => {
    const user = userEvent.setup();
    // Make the API call hang indefinitely
    mockPost.mockReturnValue(new Promise(() => {}));
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /sending reset link/i })
      ).toBeDisabled();
    });
  });

  it("renders the mail icon on success screen", async () => {
    const user = userEvent.setup();
    render(<ForgotPasswordPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    await waitFor(() => {
      expect(screen.getByTestId("mail-icon")).toBeInTheDocument();
    });
  });
});
