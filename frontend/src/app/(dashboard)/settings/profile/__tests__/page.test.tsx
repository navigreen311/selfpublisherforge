import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mocks — must be set up before component imports ──────────────────────

const mockMutateAsync = jest.fn();
const mockDeleteMutateAsync = jest.fn();
const mockUseCurrentUser = jest.fn();
const mockUseUpdateProfile = jest.fn();
const mockUseDeleteAccount = jest.fn();
const mockLogout = jest.fn();
const mockPush = jest.fn();

// Mock the users hooks module
jest.mock("@/modules/users/hooks", () => ({
  useCurrentUser: (...args: unknown[]) => mockUseCurrentUser(...args),
  useUpdateProfile: (...args: unknown[]) => mockUseUpdateProfile(...args),
  useDeleteAccount: (...args: unknown[]) => mockUseDeleteAccount(...args),
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

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock auth store
jest.mock("@/lib/store", () => ({
  useAuthStore: (selector: (state: { logout: () => void }) => unknown) =>
    selector({ logout: mockLogout }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// ── Import after mocks ──────────────────────────────────────────────────

import ProfileSettingsPage from "../page";

// ── Test Data ────────────────────────────────────────────────────────────

const mockUser = {
  id: "1",
  email: "test@test.com",
  name: "Test User",
  avatar_url: "https://example.com/avatar.png",
  role: "owner",
  org_id: "org-1",
  preferences: {
    bio: "Author bio",
    timezone: "UTC",
    language: "en",
    pen_names: [{ name: "Jane Author" }],
    social_links: {
      website: "https://example.com",
      twitter: "https://twitter.com/test",
      amazon_author_page: "https://amazon.com/author/test",
    },
  },
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
    mockDeleteMutateAsync.mockResolvedValue({});
    mockUseCurrentUser.mockReturnValue({
      data: mockUser,
      isLoading: false,
      error: null,
    });
    mockUseUpdateProfile.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    });
    mockUseDeleteAccount.mockReturnValue({
      mutateAsync: mockDeleteMutateAsync,
      isPending: false,
    });
  });

  // 1. Renders profile form with all fields
  it("renders profile form with all user data", () => {
    render(<ProfileSettingsPage />);

    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Update your personal information and display preferences."
      )
    ).toBeInTheDocument();

    // Basic fields
    expect(screen.getByLabelText("Email")).toHaveValue("test@test.com");
    expect(screen.getByLabelText("Display Name")).toHaveValue("Test User");
    expect(screen.getByLabelText("Bio")).toHaveValue("Author bio");

    // Pen names
    expect(screen.getByDisplayValue("Jane Author")).toBeInTheDocument();

    // Social links
    expect(screen.getByLabelText("Website")).toHaveValue(
      "https://example.com"
    );
  });

  // 2. Email field is disabled
  it("email field is disabled and displays helper text", () => {
    render(<ProfileSettingsPage />);

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    expect(emailInput).toBeDisabled();
    expect(
      screen.getByText("Email cannot be changed here.")
    ).toBeInTheDocument();
  });

  // 3. Display name is editable
  it("allows editing the display name", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const nameInput = screen.getByLabelText("Display Name");
    await user.clear(nameInput);
    await user.type(nameInput, "Updated Name");

    expect(nameInput).toHaveValue("Updated Name");
  });

  // 4. Bio is editable
  it("allows editing the bio", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const bioInput = screen.getByLabelText("Bio");
    await user.clear(bioInput);
    await user.type(bioInput, "New bio text");

    expect(bioInput).toHaveValue("New bio text");
  });

  // 5. Timezone can be changed
  it("displays timezone selector", () => {
    render(<ProfileSettingsPage />);
    expect(screen.getByText("Timezone")).toBeInTheDocument();
  });

  // 6. Language can be changed
  it("displays language selector", () => {
    render(<ProfileSettingsPage />);
    expect(screen.getByText("Preferred Language")).toBeInTheDocument();
  });

  // 7. Can add pen names
  it("allows adding new pen names", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const addButton = screen.getByRole("button", { name: /add pen name/i });
    await user.click(addButton);

    // Should have 2 pen name inputs now (1 existing + 1 new)
    const penNameInputs = screen.getAllByPlaceholderText("Jane Doe");
    expect(penNameInputs).toHaveLength(2);
  });

  // 8. Can remove pen names
  it("allows removing pen names", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const removeButton = screen.getByRole("button", {
      name: /remove pen name/i,
    });
    await user.click(removeButton);

    // Pen name should be removed
    await waitFor(() => {
      expect(screen.queryByDisplayValue("Jane Author")).not.toBeInTheDocument();
    });
  });

  // 9. Social links are editable
  it("allows editing social links", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const websiteInput = screen.getByLabelText("Website");
    await user.clear(websiteInput);
    await user.type(websiteInput, "https://newsite.com");

    expect(websiteInput).toHaveValue("https://newsite.com");
  });

  // 10. Form submission with all fields
  it("submits form with all updated fields", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    // Update name
    const nameInput = screen.getByLabelText("Display Name");
    await user.clear(nameInput);
    await user.type(nameInput, "New Name");

    // Submit
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "New Name",
          preferences: expect.objectContaining({
            bio: "Author bio",
            timezone: "UTC",
            language: "en",
          }),
        })
      );
    });
  });

  // 11. Success toast on save
  it("shows success toast on successful save", async () => {
    const user = userEvent.setup();
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

  // 12. Error toast on failed save
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
      expect(mockToastError).toHaveBeenCalledWith("Failed to update profile");
    });
  });

  // 13. Save button disabled when pristine
  it("save button is disabled when form is not dirty", () => {
    render(<ProfileSettingsPage />);

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    expect(saveButton).toBeDisabled();
  });

  // 14. Shows loading state
  it("shows loading skeleton when user data is loading", () => {
    mockUseCurrentUser.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    const { container } = render(<ProfileSettingsPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  // 15. Displays user role
  it("displays user role", () => {
    render(<ProfileSettingsPage />);
    expect(screen.getByText("owner")).toBeInTheDocument();
  });

  // 16. Renders Danger Zone
  it("renders danger zone section", () => {
    render(<ProfileSettingsPage />);
    expect(screen.getByText("Danger Zone")).toBeInTheDocument();
    // The heading and the button inside it share the text.
    expect(screen.getAllByText("Delete Account").length).toBeGreaterThan(0);
  });

  // 17. Delete account dialog opens
  it("opens delete account dialog when clicking delete button", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    const deleteButton = screen.getByRole("button", {
      name: /delete account/i,
    });
    await user.click(deleteButton);

    await waitFor(() => {
      expect(
        screen.getByText("Are you absolutely sure?")
      ).toBeInTheDocument();
    });
  });

  // 18. Delete account requires password and confirmation
  it("requires password and confirmation text to delete account", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    // Open first dialog
    const deleteButton = screen.getByRole("button", {
      name: /delete account/i,
    });
    await user.click(deleteButton);

    // Confirm first dialog
    const confirmButton = screen.getByRole("button", {
      name: /yes, i want to delete my account/i,
    });
    await user.click(confirmButton);

    // Should show second dialog
    await waitFor(() => {
      expect(
        screen.getByText("Final Confirmation Required")
      ).toBeInTheDocument();
    });

    // Fill in password and confirmation
    const passwordInput = screen.getByLabelText("Password");
    await user.type(passwordInput, "mypassword");

    const confirmInput = screen.getByPlaceholderText("DELETE");
    await user.type(confirmInput, "DELETE");

    // Click final delete button
    const finalDeleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    expect(finalDeleteButton).not.toBeDisabled();
  });

  // 19. Account deletion triggers mutation
  it("triggers delete account mutation with password", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    // Open dialogs
    const deleteButton = screen.getByRole("button", {
      name: /delete account/i,
    });
    await user.click(deleteButton);

    const confirmButton = screen.getByRole("button", {
      name: /yes, i want to delete my account/i,
    });
    await user.click(confirmButton);

    // Fill in and submit
    const passwordInput = screen.getByLabelText("Password");
    await user.type(passwordInput, "mypassword");

    const confirmInput = screen.getByPlaceholderText("DELETE");
    await user.type(confirmInput, "DELETE");

    const finalDeleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    await user.click(finalDeleteButton);

    await waitFor(() => {
      expect(mockDeleteMutateAsync).toHaveBeenCalledWith("mypassword");
    });
  });

  // 20. Account deletion logs out and redirects
  it("logs out and redirects after successful account deletion", async () => {
    const user = userEvent.setup();
    render(<ProfileSettingsPage />);

    // Go through delete flow
    const deleteButton = screen.getByRole("button", {
      name: /delete account/i,
    });
    await user.click(deleteButton);

    const confirmButton = screen.getByRole("button", {
      name: /yes, i want to delete my account/i,
    });
    await user.click(confirmButton);

    const passwordInput = screen.getByLabelText("Password");
    await user.type(passwordInput, "mypassword");

    const confirmInput = screen.getByPlaceholderText("DELETE");
    await user.type(confirmInput, "DELETE");

    const finalDeleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    await user.click(finalDeleteButton);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });
});
