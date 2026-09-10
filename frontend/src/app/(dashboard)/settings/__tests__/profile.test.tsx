import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mocks — must be set up before component imports ──────────────────────

const mockMutateAsync = jest.fn();
const mockUseCurrentUser = jest.fn();
const mockUseUpdateProfile = jest.fn();

// Mock the users hooks module
// The pages call useRouter/useSearchParams; without a mock next throws
// "invariant expected app router to be mounted" and the render dies.
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

jest.mock("@/modules/users/hooks", () => ({
  useCurrentUser: (...args: unknown[]) => mockUseCurrentUser(...args),
  useUpdateProfile: (...args: unknown[]) => mockUseUpdateProfile(...args),
  useDeleteAccount: () => ({ mutate: jest.fn(), mutateAsync: jest.fn().mockResolvedValue({}), isPending: false, isError: false, error: null, reset: jest.fn() }),
}));

// Mock sonner toast
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();
jest.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// ── Import after mocks ──────────────────────────────────────────────────

import ProfileSettingsPage from "../../settings/profile/page";

// ── Test Data ────────────────────────────────────────────────────────────

const mockUser = {
  id: "1",
  email: "test@test.com",
  name: "Test User",
  avatar_url: null,
  role: "owner",
  org_id: "org-1",
  preferences: {},
  is_active: true,
  mfa_enabled: false,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

// ── Tests ────────────────────────────────────────────────────────────────

describe("ProfileSettingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockMutateAsync.mockResolvedValue(mockUser);
    mockUseCurrentUser.mockReturnValue({
      data: mockUser,
      isLoading: false,
      error: null,
    });
    mockUseUpdateProfile.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    });
  });

  // 1. Renders profile form with user data
  it("renders profile form with user data", () => {
    render(<ProfileSettingsPage />);

    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Update your personal information and display preferences."
      )
    ).toBeInTheDocument();

    // Email field displays user email and is disabled
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    expect(emailInput).toBeInTheDocument();
    expect(emailInput.value).toBe("test@test.com");
    expect(emailInput).toBeDisabled();

    // Name field displays user name
    const nameInput = screen.getByLabelText("Display Name") as HTMLInputElement;
    expect(nameInput).toBeInTheDocument();
    expect(nameInput.value).toBe("Test User");
  });

  // 2. Name field is editable
  it("allows editing the name field", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const nameInput = screen.getByLabelText("Display Name") as HTMLInputElement;
    expect(nameInput).not.toBeDisabled();

    await user.clear(nameInput);
    await user.type(nameInput, "Updated Name");

    expect(nameInput.value).toBe("Updated Name");
  });

  // 3. Email field displays correctly
  it("email field displays correctly and is disabled", () => {
    render(<ProfileSettingsPage />);

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    expect(emailInput).toBeDisabled();
    expect(emailInput.value).toBe("test@test.com");
    expect(
      screen.getByText("Email cannot be changed here.")
    ).toBeInTheDocument();
  });

  // 4. Save button triggers update
  it("save button triggers update mutation on submit", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    // Change name to make form dirty
    const nameInput = screen.getByLabelText("Display Name");
    await user.clear(nameInput);
    await user.type(nameInput, "New Name");

    // Submit form
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    expect(saveButton).not.toBeDisabled();
    await user.click(saveButton);

    await waitFor(() => {
      // The form also submits the preferences block (bio, pen names, links).
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({ name: "New Name", avatar_url: null })
      );
    });
  });

  // 5. Success toast on save
  it("shows success toast on successful save", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockUser);

    render(<ProfileSettingsPage />);

    const nameInput = screen.getByLabelText("Display Name");
    await user.clear(nameInput);
    await user.type(nameInput, "New Name");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith(
        "Profile updated successfully"
      );
    });
  });

  // Additional: error toast on failed save
  it("shows error toast when save fails", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockRejectedValue(new Error("Update failed"));

    render(<ProfileSettingsPage />);

    const nameInput = screen.getByLabelText("Display Name");
    await user.clear(nameInput);
    await user.type(nameInput, "New Name");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(
        "Failed to update profile"
      );
    });
  });

  // Additional: loading state
  it("shows loading skeleton when user data is loading", () => {
    mockUseCurrentUser.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { container } = render(<ProfileSettingsPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  // Additional: save button disabled when form is pristine
  it("save button is disabled when form is not dirty", () => {
    render(<ProfileSettingsPage />);

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    expect(saveButton).toBeDisabled();
  });

  // Additional: shows user role
  it("displays user role", () => {
    render(<ProfileSettingsPage />);
    expect(screen.getByText("owner")).toBeInTheDocument();
  });
});
