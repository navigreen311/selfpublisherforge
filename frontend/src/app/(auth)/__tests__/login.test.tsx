import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
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

const mockLogin = jest.fn();
const mockLoginWithGoogle = jest.fn();
const mockLoginWithGitHub = jest.fn();

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    login: mockLogin,
    register: jest.fn(),
    logout: jest.fn(),
    checkAuth: jest.fn(),
    loginWithGoogle: mockLoginWithGoogle,
    loginWithGitHub: mockLoginWithGitHub,
    handleOAuthCallback: jest.fn(),
    user: null,
    isAuthenticated: false,
    isLoading: false,
  }),
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

// Mock @radix-ui/react-switch for the Switch component
jest.mock("@radix-ui/react-switch", () => ({
  Root: React.forwardRef(
    (
      {
        children,
        checked,
        onCheckedChange,
        id,
        ...props
      }: {
        children?: React.ReactNode;
        checked?: boolean;
        onCheckedChange?: (checked: boolean) => void;
        id?: string;
      } & Record<string, unknown>,
      ref: React.Ref<HTMLButtonElement>
    ) => (
      <button
        ref={ref}
        role="switch"
        aria-checked={checked}
        id={id}
        onClick={() => onCheckedChange?.(!checked)}
        data-state={checked ? "checked" : "unchecked"}
        {...props}
      >
        {children}
      </button>
    )
  ),
  Thumb: ({ ...props }: Record<string, unknown>) => <span {...props} />,
}));

// ─── Import after mocks ─────────────────────────────────────────────────────

import LoginPage from "../login/page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogin.mockResolvedValue(undefined);
  });

  it("renders login form with email and password fields", () => {
    render(<LoginPage />);

    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(
      screen.getByText("Sign in to your SelfPublisherForge account")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("you@example.com")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Enter your password")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("shows validation errors for empty fields (native required)", async () => {
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText("you@example.com");
    const passwordInput = screen.getByPlaceholderText("Enter your password");

    // Both inputs have the required attribute
    expect(emailInput).toBeRequired();
    expect(passwordInput).toBeRequired();
  });

  it("calls login on form submit with correct credentials", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Enter your password"),
      "MyPassword123"
    );
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "MyPassword123",
        mfaCode: undefined,
        rememberMe: false,
      });
    });
  });

  it("shows error message on failed login", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("Invalid email or password"));
    render(<LoginPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Enter your password"),
      "WrongPassword1"
    );
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Invalid email or password")
      ).toBeInTheDocument();
    });
  });

  it("has link to register page", () => {
    render(<LoginPage />);

    const registerLink = screen.getByRole("link", {
      name: /create account/i,
    });
    expect(registerLink).toBeInTheDocument();
    expect(registerLink).toHaveAttribute("href", "/register");
  });

  it("has link to forgot password", () => {
    render(<LoginPage />);

    const forgotLink = screen.getByRole("link", {
      name: /forgot password/i,
    });
    expect(forgotLink).toBeInTheDocument();
    expect(forgotLink).toHaveAttribute("href", "/forgot-password");
  });

  it("renders OAuth buttons (Google, GitHub)", () => {
    render(<LoginPage />);

    expect(
      screen.getByRole("button", { name: /google/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /github/i })
    ).toBeInTheDocument();
  });

  it("calls loginWithGoogle when Google button is clicked", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.click(screen.getByRole("button", { name: /google/i }));
    expect(mockLoginWithGoogle).toHaveBeenCalled();
  });

  it("calls loginWithGitHub when GitHub button is clicked", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.click(screen.getByRole("button", { name: /github/i }));
    expect(mockLoginWithGitHub).toHaveBeenCalled();
  });

  it("toggles password visibility when eye button is clicked", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const passwordInput = screen.getByPlaceholderText("Enter your password");
    expect(passwordInput).toHaveAttribute("type", "password");

    // Click the toggle button (it contains the eye icon)
    const toggleButton = screen.getByTestId("eye-icon").closest("button")!;
    await user.click(toggleButton);

    expect(passwordInput).toHaveAttribute("type", "text");
  });

  it("renders the remember me switch", () => {
    render(<LoginPage />);

    expect(screen.getByText("Remember me")).toBeInTheDocument();
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  it("shows MFA input when login returns an MFA error", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("MFA code required"));
    render(<LoginPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Enter your password"),
      "MyPassword123"
    );
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter 6-digit code")
      ).toBeInTheDocument();
    });
  });

  it("submits with MFA code when MFA field is visible", async () => {
    const user = userEvent.setup();
    // First call triggers MFA, second call succeeds
    mockLogin
      .mockRejectedValueOnce(new Error("MFA code required"))
      .mockResolvedValueOnce(undefined);

    render(<LoginPage />);

    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Enter your password"),
      "MyPassword123"
    );
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    // Wait for MFA input to appear
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter 6-digit code")
      ).toBeInTheDocument();
    });

    // Enter MFA code and submit again
    await user.type(
      screen.getByPlaceholderText("Enter 6-digit code"),
      "123456"
    );
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenLastCalledWith({
        email: "test@example.com",
        password: "MyPassword123",
        mfaCode: "123456",
        rememberMe: false,
      });
    });
  });

  it("displays 'Or continue with' separator text", () => {
    render(<LoginPage />);

    expect(screen.getByText("Or continue with")).toBeInTheDocument();
  });
});
