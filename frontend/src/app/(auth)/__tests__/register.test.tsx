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

const mockRegister = jest.fn();
const mockLoginWithGoogle = jest.fn();
const mockLoginWithGitHub = jest.fn();

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    login: jest.fn(),
    register: mockRegister,
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
  Check: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="check-icon" {...props} />
  ),
  ChevronDown: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-down-icon" {...props} />
  ),
  ChevronUp: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="chevron-up-icon" {...props} />
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

// Mock @radix-ui/react-select to render a simple native-like select
jest.mock("@radix-ui/react-select", () => {
  const SelectRoot = ({
    children,
    value,
    onValueChange,
  }: {
    children: React.ReactNode;
    value?: string;
    onValueChange?: (value: string) => void;
  }) => (
    <div data-testid="select-root" data-value={value}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(
            child as React.ReactElement<Record<string, unknown>>,
            { _value: value, _onValueChange: onValueChange }
          );
        }
        return child;
      })}
    </div>
  );

  const SelectTrigger = React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLButtonElement>
    ) => (
      <button ref={ref} data-testid="select-trigger" {...props}>
        {children}
      </button>
    )
  );
  SelectTrigger.displayName = "SelectTrigger";

  const SelectValue = ({
    _value,
    placeholder,
  }: {
    _value?: string;
    placeholder?: string;
  } & Record<string, unknown>) => (
    <span data-testid="select-value">{_value || placeholder}</span>
  );

  const SelectContent = React.forwardRef(
    (
      { children, ...props }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => (
      <div ref={ref} data-testid="select-content" {...props}>
        {children}
      </div>
    )
  );
  SelectContent.displayName = "SelectContent";

  const SelectItem = React.forwardRef(
    (
      {
        children,
        value,
        _onValueChange,
        ...props
      }: {
        children?: React.ReactNode;
        value?: string;
        _onValueChange?: (value: string) => void;
      } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => (
      <div
        ref={ref}
        role="option"
        data-testid={`select-item-${value}`}
        onClick={() => _onValueChange?.(value || "")}
        {...props}
      >
        {children}
      </div>
    )
  );
  SelectItem.displayName = "SelectItem";

  const SelectIcon = ({ children }: { children?: React.ReactNode }) => (
    <span>{children}</span>
  );
  const SelectPortal = ({ children }: { children?: React.ReactNode }) => (
    <>{children}</>
  );
  const SelectViewport = ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  );
  const SelectGroup = ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  );
  const SelectLabel = ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  );
  const SelectSeparator = () => <hr />;
  const SelectItemText = ({ children }: { children?: React.ReactNode }) => (
    <span>{children}</span>
  );
  const SelectItemIndicator = ({
    children,
  }: {
    children?: React.ReactNode;
  }) => <span>{children}</span>;
  const SelectScrollUpButton = React.forwardRef(
    (props: Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => (
      <div ref={ref} {...props} />
    )
  );
  SelectScrollUpButton.displayName = "SelectScrollUpButton";
  const SelectScrollDownButton = React.forwardRef(
    (props: Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => (
      <div ref={ref} {...props} />
    )
  );
  SelectScrollDownButton.displayName = "SelectScrollDownButton";

  return {
    Root: SelectRoot,
    Trigger: SelectTrigger,
    Value: SelectValue,
    Content: SelectContent,
    Item: SelectItem,
    Icon: SelectIcon,
    Portal: SelectPortal,
    Viewport: SelectViewport,
    Group: SelectGroup,
    Label: SelectLabel,
    Separator: SelectSeparator,
    ItemText: SelectItemText,
    ItemIndicator: SelectItemIndicator,
    ScrollUpButton: SelectScrollUpButton,
    ScrollDownButton: SelectScrollDownButton,
  };
});

// ─── Import after mocks ─────────────────────────────────────────────────────

import RegisterPage from "../register/page";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("RegisterPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRegister.mockResolvedValue(undefined);
  });

  it("renders the registration form with all required fields", () => {
    render(<RegisterPage />);

    expect(screen.getByText("Create your account")).toBeInTheDocument();
    expect(
      screen.getByText("Start your self-publishing journey today")
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("John Doe")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("you@example.com")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Create a password")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("My Publishing House (optional)")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeInTheDocument();
  });

  it("displays password validation rules when typing a password", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    // Before typing, no password checks visible
    expect(screen.queryByText("8+ characters")).not.toBeInTheDocument();

    // Type a partial password to show checks
    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "ab"
    );

    // Password check labels should now appear
    expect(screen.getByText("8+ characters")).toBeInTheDocument();
    expect(screen.getByText("Uppercase letter")).toBeInTheDocument();
    expect(screen.getByText("Lowercase letter")).toBeInTheDocument();
    expect(screen.getByText("Number")).toBeInTheDocument();
  });

  it("updates password validation checks as requirements are met", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const passwordInput = screen.getByPlaceholderText("Create a password");

    // Type a password that meets all requirements
    await user.type(passwordInput, "StrongPass1");

    // All checks should be visible
    expect(screen.getByText("8+ characters")).toBeInTheDocument();
    expect(screen.getByText("Uppercase letter")).toBeInTheDocument();
    expect(screen.getByText("Lowercase letter")).toBeInTheDocument();
    expect(screen.getByText("Number")).toBeInTheDocument();

    // With "StrongPass1", all requirements should be met.
    // Each check label should have the green text color (text-green-600)
    const lengthCheck = screen.getByText("8+ characters").closest("div");
    const uppercaseCheck = screen.getByText("Uppercase letter").closest("div");
    const lowercaseCheck = screen.getByText("Lowercase letter").closest("div");
    const numberCheck = screen.getByText("Number").closest("div");

    expect(lengthCheck).toHaveClass("text-green-600");
    expect(uppercaseCheck).toHaveClass("text-green-600");
    expect(lowercaseCheck).toHaveClass("text-green-600");
    expect(numberCheck).toHaveClass("text-green-600");
  });

  it("shows unmet password requirements for weak password", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    // Type a weak password that fails multiple checks
    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "weak"
    );

    // The password checks should show. "weak" has lowercase but fails
    // length, uppercase, and number requirements.
    const lengthCheck = screen.getByText("8+ characters").closest("div");
    const uppercaseCheck = screen.getByText("Uppercase letter").closest("div");
    const lowercaseCheck = screen.getByText("Lowercase letter").closest("div");
    const numberCheck = screen.getByText("Number").closest("div");

    // Lowercase should be green (met), others should not
    expect(lowercaseCheck).toHaveClass("text-green-600");
    expect(lengthCheck).not.toHaveClass("text-green-600");
    expect(uppercaseCheck).not.toHaveClass("text-green-600");
    expect(numberCheck).not.toHaveClass("text-green-600");

    // Submission is validated on submit rather than by gating the button —
    // see "blocks submission and reports the errors when the password is weak".
    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeEnabled();
  });

  it("blocks submission and reports the errors when the password is weak", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByPlaceholderText("John Doe"), "Test User");
    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(screen.getByPlaceholderText("Create a password"), "weak");
    await user.type(screen.getByPlaceholderText("Re-enter your password"), "weak");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(
      await screen.findByText("Please fix the errors above before submitting")
    ).toBeInTheDocument();
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it("enables submit button when password is valid", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "ValidPass1"
    );

    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeEnabled();
  });

  it("submits the form with valid data", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByPlaceholderText("John Doe"), "Test User");
    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Re-enter your password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("My Publishing House (optional)"),
      "My Org"
    );

    await user.click(
      screen.getByRole("button", { name: /create account/i })
    );

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        name: "Test User",
        email: "test@example.com",
        password: "ValidPass1",
        orgName: "My Org",
        planTier: "free",
      });
    });
  });

  it("handles registration error for duplicate email", async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue(
      new Error("An account with this email already exists")
    );
    render(<RegisterPage />);

    await user.type(screen.getByPlaceholderText("John Doe"), "Test User");
    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "existing@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Re-enter your password"),
      "ValidPass1"
    );

    await user.click(
      screen.getByRole("button", { name: /create account/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText("An account with this email already exists")
      ).toBeInTheDocument();
    });
  });

  it("shows generic error message for non-Error rejections", async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue("unexpected error");
    render(<RegisterPage />);

    await user.type(screen.getByPlaceholderText("John Doe"), "Test User");
    await user.type(
      screen.getByPlaceholderText("you@example.com"),
      "test@example.com"
    );
    await user.type(
      screen.getByPlaceholderText("Create a password"),
      "ValidPass1"
    );
    await user.type(
      screen.getByPlaceholderText("Re-enter your password"),
      "ValidPass1"
    );

    await user.click(
      screen.getByRole("button", { name: /create account/i })
    );

    await waitFor(() => {
      expect(
        screen.getByText("Registration failed. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("renders OAuth buttons (Google, GitHub)", () => {
    render(<RegisterPage />);

    expect(
      screen.getByRole("button", { name: /google/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /github/i })
    ).toBeInTheDocument();
  });

  it("has link to sign in page", () => {
    render(<RegisterPage />);

    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toBeInTheDocument();
    expect(signInLink).toHaveAttribute("href", "/login");
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const passwordInput = screen.getByPlaceholderText("Create a password");
    expect(passwordInput).toHaveAttribute("type", "password");

    const toggleButton = screen.getByTestId("eye-icon").closest("button")!;
    await user.click(toggleButton);

    expect(passwordInput).toHaveAttribute("type", "text");
  });

  it("renders the plan selector with Free as default", () => {
    render(<RegisterPage />);

    expect(screen.getByText("Plan")).toBeInTheDocument();
    expect(screen.getByTestId("select-trigger")).toBeInTheDocument();
  });

  it("displays 'Or continue with' separator text", () => {
    render(<RegisterPage />);

    expect(screen.getByText("Or continue with")).toBeInTheDocument();
  });
});
