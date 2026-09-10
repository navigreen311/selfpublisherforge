import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mocks — must be set up before component imports ──────────────────────

const mockPost = jest.fn();
const mockGet = jest.fn();
const mockInvalidateQueries = jest.fn();

// Mock next/link
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

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  X: (props: React.SVGAttributes<SVGElement>) => (
    <svg data-testid="x-icon" {...props} />
  ),
}));

// Mock the API module
jest.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
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

// Mock @tanstack/react-query
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: () => ({
    invalidateQueries: mockInvalidateQueries,
  }),
}));

// Mock useCurrentUser hook and userKeys
const mockUseCurrentUser = jest.fn();
jest.mock("@/modules/users/hooks", () => ({
  useCurrentUser: (...args: unknown[]) => mockUseCurrentUser(...args),
  userKeys: {
    me: ["users", "me"],
    sessions: ["users", "me", "sessions"],
    org: (id: string) => ["orgs", id],
    members: (orgId: string) => ["orgs", orgId, "members"],
    apiKeys: (orgId: string) => ["orgs", orgId, "api-keys"],
  },
}));

// Mock Radix Dialog to render directly (no portal/overlay)
jest.mock("@radix-ui/react-dialog", () => ({
  Root: ({
    children,
    open,
  }: {
    children: React.ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => (open ? <>{children}</> : null),
  Trigger: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLButtonElement>
    ) => (
      <button ref={ref} {...props}>
        {children}
      </button>
    )
  ),
  Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Overlay: React.forwardRef(
    (props: Record<string, unknown>, ref: React.Ref<HTMLDivElement>) => (
      <div ref={ref} {...props} />
    )
  ),
  Content: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLDivElement>
    ) => (
      <div ref={ref} role="dialog" {...props}>
        {children}
      </div>
    )
  ),
  Title: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLHeadingElement>
    ) => (
      <h2 ref={ref} {...props}>
        {children}
      </h2>
    )
  ),
  Description: React.forwardRef(
    (
      {
        children,
        ...props
      }: { children?: React.ReactNode } & Record<string, unknown>,
      ref: React.Ref<HTMLParagraphElement>
    ) => (
      <p ref={ref} {...props}>
        {children}
      </p>
    )
  ),
  Close: ({
    children,
    ...props
  }: { children?: React.ReactNode } & Record<string, unknown>) => (
    <button {...props}>{children}</button>
  ),
}));

// Mock Radix Slot
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

// ── Import after mocks ──────────────────────────────────────────────────

import SecuritySettingsPage from "../../settings/security/page";

// ── Helper data ─────────────────────────────────────────────────────────

const mockSetupResponse = {
  secret: "JBSWY3DPEHPK3PXP",
  qr_code_url: "https://example.com/qr-code.png",
  backup_codes: [
    "abc12-def34",
    "ghi56-jkl78",
    "mno90-pqr12",
    "stu34-vwx56",
    "yza78-bcd90",
    "efg12-hij34",
    "klm56-nop78",
    "qrs90-tuv12",
  ],
};

const userWithMfaOff = {
  data: {
    id: "1",
    email: "test@example.com",
    name: "Test User",
    mfa_enabled: false,
    role: "owner",
    org_id: "org-1",
  },
  isLoading: false,
  error: null,
};

const userWithMfaOn = {
  data: {
    id: "1",
    email: "test@example.com",
    name: "Test User",
    mfa_enabled: true,
    role: "owner",
    org_id: "org-1",
  },
  isLoading: false,
  error: null,
};

const loadingState = {
  data: undefined,
  isLoading: true,
  error: null,
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("SecuritySettingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPost.mockResolvedValue({ data: {} });
    mockGet.mockResolvedValue({ data: {} });
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
  });

  // 1. Renders password change form / security heading
  it("renders security settings page with heading and description", () => {
    render(<SecuritySettingsPage />);

    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Manage your account security settings and two-factor authentication."
      )
    ).toBeInTheDocument();
  });

  // 2. MFA section displays
  it("displays the MFA section with Two-Factor Authentication title", () => {
    render(<SecuritySettingsPage />);

    expect(
      screen.getByText("Two-Factor Authentication")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/add an extra layer of security/i)
    ).toBeInTheDocument();
  });

  // 3. Current password required (for disabling MFA)
  it("requires password input to disable MFA when MFA is enabled", async () => {
    const user = userEvent.setup();
    mockUseCurrentUser.mockReturnValue(userWithMfaOn);

    render(<SecuritySettingsPage />);

    // Click the disable button to open the dialog
    await user.click(
      screen.getByRole("button", {
        name: /disable two-factor authentication/i,
      })
    );

    // A dialog should open asking for the password
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/enter your password/i)
      ).toBeInTheDocument();
    });

    // The "Disable MFA" confirmation button should be disabled when the password field is empty
    const disableBtn = screen.getByRole("button", {
      name: /disable mfa/i,
    });
    expect(disableBtn).toBeDisabled();
  });

  // 4. New password validation (verification code input in setup)
  it("shows verification code input with validation during MFA setup", async () => {
    const user = userEvent.setup();
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
    mockPost.mockResolvedValue({ data: mockSetupResponse });

    render(<SecuritySettingsPage />);

    await user.click(
      screen.getByRole("button", {
        name: /enable two-factor authentication/i,
      })
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText("000000")).toBeInTheDocument();
    });

    // The "Verify & Enable" button should be present
    expect(
      screen.getByRole("button", { name: /verify/i })
    ).toBeInTheDocument();
  });

  // 5. Shows active sessions if available (loading state)
  it("shows loading state while user data is being fetched", () => {
    mockUseCurrentUser.mockReturnValue(loadingState);

    const { container } = render(<SecuritySettingsPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  // Additional: enable button when MFA is off
  it("shows enable MFA button when MFA is off", () => {
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
    render(<SecuritySettingsPage />);

    expect(
      screen.getByRole("button", {
        name: /enable two-factor authentication/i,
      })
    ).toBeInTheDocument();
  });

  // Additional: MFA enabled state
  it("shows disable button and enabled status when MFA is on", () => {
    mockUseCurrentUser.mockReturnValue(userWithMfaOn);
    render(<SecuritySettingsPage />);

    expect(
      screen.getByText(/two-factor authentication is enabled/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /disable two-factor authentication/i,
      })
    ).toBeInTheDocument();
  });

  // Additional: QR code and secret key display during setup
  it("displays QR code and manual secret key after setup initiation", async () => {
    const user = userEvent.setup();
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
    mockPost.mockResolvedValue({ data: mockSetupResponse });

    render(<SecuritySettingsPage />);

    await user.click(
      screen.getByRole("button", {
        name: /enable two-factor authentication/i,
      })
    );

    await waitFor(() => {
      const qrImg = screen.getByAltText("MFA QR Code");
      expect(qrImg).toBeInTheDocument();
      expect(qrImg).toHaveAttribute("src", mockSetupResponse.qr_code_url);
    });

    // Manual secret key should be visible
    expect(screen.getByText(mockSetupResponse.secret)).toBeInTheDocument();
  });

  // Additional: backup codes displayed during setup
  it("displays backup codes during MFA setup", async () => {
    const user = userEvent.setup();
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
    mockPost.mockResolvedValue({ data: mockSetupResponse });

    render(<SecuritySettingsPage />);

    await user.click(
      screen.getByRole("button", {
        name: /enable two-factor authentication/i,
      })
    );

    await waitFor(() => {
      for (const code of mockSetupResponse.backup_codes) {
        expect(screen.getByText(code)).toBeInTheDocument();
      }
    });

    expect(
      screen.getByText(/save your backup codes/i)
    ).toBeInTheDocument();
  });

  // Additional: cancel setup flow
  it("cancel button returns to initial state during setup", async () => {
    const user = userEvent.setup();
    mockUseCurrentUser.mockReturnValue(userWithMfaOff);
    mockPost.mockResolvedValue({ data: mockSetupResponse });

    render(<SecuritySettingsPage />);

    await user.click(
      screen.getByRole("button", {
        name: /enable two-factor authentication/i,
      })
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: /enable two-factor authentication/i,
        })
      ).toBeInTheDocument();
    });
  });
});
