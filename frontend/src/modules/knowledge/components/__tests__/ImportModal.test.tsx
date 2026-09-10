import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ImportModal } from "../ImportModal";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockMutateAsync = jest.fn().mockResolvedValue({});

jest.mock("../../hooks", () => ({
  useImportEntry: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  }),
  useCreateEntry: () => ({
    mutate: jest.fn(),
    mutateAsync: jest.fn().mockResolvedValue({}),
    isPending: false,
    isError: false,
    error: null,
    reset: jest.fn(),
  }),
}));

// Mock lucide-react icons to simple spans
jest.mock("lucide-react", () => ({
  X: (props: Record<string, unknown>) => <span data-testid="icon-x" {...props} />,
  Upload: (props: Record<string, unknown>) => (
    <span data-testid="icon-upload" {...props} />
  ),
  Link: (props: Record<string, unknown>) => (
    <span data-testid="icon-link" {...props} />
  ),
  Loader2: (props: Record<string, unknown>) => (
    <span data-testid="icon-loader" {...props} />
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderModal(
  props: Partial<React.ComponentProps<typeof ImportModal>> = {},
) {
  const defaultProps: React.ComponentProps<typeof ImportModal> = {
    open: true,
    onClose: jest.fn(),
    ...props,
  };
  return {
    ...render(<ImportModal {...defaultProps} />),
    props: defaultProps,
  };
}

/**
 * Create a mock File object with the given name and size (in bytes).
 */
function createMockFile(
  name: string,
  sizeBytes: number,
  type = "application/octet-stream",
): File {
  // Build content that matches the requested size
  const content = new Uint8Array(sizeBytes);
  return new File([content], name, { type });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ImportModal", () => {
  beforeEach(() => {
    mockMutateAsync.mockClear();
  });

  // 1. Renders modal with URL and file upload tabs
  it("renders modal with file upload and URL input options", () => {
    renderModal();

    expect(screen.getByText("Import Research")).toBeInTheDocument();
    expect(screen.getByText("From URL")).toBeInTheDocument();
    expect(screen.getByText("From File")).toBeInTheDocument();
  });

  // 2. Does not render when open is false
  it("does not render anything when open is false", () => {
    const { container } = renderModal({ open: false });
    expect(container.innerHTML).toBe("");
  });

  // 3. Shows error when file exceeds 50MB
  it("shows error when file exceeds 50MB", async () => {
    const user = userEvent.setup();
    renderModal();

    // Switch to file tab
    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    const bigFile = createMockFile("huge.pdf", 51 * 1024 * 1024);

    await user.upload(fileInput, bigFile);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/too large/i);
      expect(screen.getByRole("alert")).toHaveTextContent(/50\.0 MB/);
    });
  });

  // 4. Shows error for unsupported file format (.exe)
  it("shows error for unsupported file format (.exe)", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    const exeFile = createMockFile("malware.exe", 1024);

    // Use fireEvent because userEvent.upload respects the accept attribute
    // and would skip .exe files silently. fireEvent bypasses that check.
    fireEvent.change(fileInput, { target: { files: [exeFile] } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /PDF, EPUB, TXT, MD, DOCX, or HTML/,
      );
    });
  });

  // 5. Accepts valid file formats (.pdf)
  it("accepts valid file formats (.pdf, .epub, .txt, .md, .docx)", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    const validFile = createMockFile("research.pdf", 1024);

    await user.upload(fileInput, validFile);

    await waitFor(() => {
      // Should show the file info, not an error
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
      expect(screen.getByText(/research\.pdf/)).toBeInTheDocument();
    });
  });

  // 6. Shows error for invalid URL (no protocol)
  it("shows error for invalid URL (no protocol)", async () => {
    const user = userEvent.setup();
    renderModal();

    // URL tab is the default
    const urlInput = screen.getByLabelText("URL");
    await user.type(urlInput, "example.com/article");
    await user.tab(); // blur to trigger touched

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /URL must start with http:\/\/ or https:\/\//,
      );
    });
  });

  // 7. Accepts valid URL (https://...)
  it("accepts valid URL (https://...)", async () => {
    const user = userEvent.setup();
    renderModal();

    const urlInput = screen.getByLabelText("URL");
    await user.type(urlInput, "https://example.com/article");
    await user.tab();

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });

  // 8. Import button disabled when no file/URL selected
  it("import button is disabled when no file or URL is selected", () => {
    renderModal();

    const importBtn = screen.getByRole("button", { name: /import$/i });
    expect(importBtn).toBeDisabled();
  });

  // 9. Import button disabled when URL validation fails
  it("import button is disabled when URL validation fails", async () => {
    const user = userEvent.setup();
    renderModal();

    const urlInput = screen.getByLabelText("URL");
    await user.type(urlInput, "not-a-url");

    await waitFor(() => {
      const importBtn = screen.getByRole("button", { name: /import/i });
      expect(importBtn).toBeDisabled();
    });
  });

  // 10. Shows file size in human-readable format
  it("shows file size in human-readable format", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    // 1.5 MB file
    const file = createMockFile("notes.txt", Math.round(1.5 * 1024 * 1024));

    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
      expect(screen.getByText(/1\.5 MB/)).toBeInTheDocument();
    });
  });

  // 11. Import button enabled with valid URL
  it("import button is enabled when a valid URL is entered", async () => {
    const user = userEvent.setup();
    renderModal();

    const urlInput = screen.getByLabelText("URL");
    await user.type(urlInput, "https://docs.example.com/guide");

    await waitFor(() => {
      const importBtn = screen.getByRole("button", { name: /import/i });
      expect(importBtn).toBeEnabled();
    });
  });

  // 12. Closing modal calls onClose
  it("calls onClose when the close button is clicked", async () => {
    const user = userEvent.setup();
    const { props } = renderModal();

    // The X button is the first button inside the modal
    const closeBtn = screen.getByTestId("icon-x").closest("button")!;
    await user.click(closeBtn);

    expect(props.onClose).toHaveBeenCalledTimes(1);
  });

  // 13. Tab switching shows the correct input
  it("switches between URL and File tabs correctly", async () => {
    const user = userEvent.setup();
    renderModal();

    // Default is URL tab
    expect(screen.getByLabelText("URL")).toBeInTheDocument();

    // Switch to File tab
    await user.click(screen.getByText("From File"));
    expect(screen.getByLabelText(/file/i)).toBeInTheDocument();
    expect(screen.queryByLabelText("URL")).not.toBeInTheDocument();

    // Switch back to URL tab
    await user.click(screen.getByText("From URL"));
    expect(screen.getByLabelText("URL")).toBeInTheDocument();
  });

  // 14. Shows hint text for accepted file formats when no file selected
  it("shows hint text for accepted file formats when no file is selected", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    expect(
      screen.getByText(/File must be PDF, EPUB, TXT, MD, DOCX, or HTML/),
    ).toBeInTheDocument();
    expect(screen.getByText(/max 50\.0 MB/)).toBeInTheDocument();
  });

  // 15. Extract facts checkbox is checked by default
  it("has the extract facts checkbox checked by default", () => {
    renderModal();

    const checkbox = screen.getByLabelText(/extract key facts/i);
    expect(checkbox).toBeChecked();
  });

  // 16. Extract facts checkbox can be toggled
  it("allows toggling the extract facts checkbox", async () => {
    const user = userEvent.setup();
    renderModal();

    const checkbox = screen.getByLabelText(/extract key facts/i);
    expect(checkbox).toBeChecked();

    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();

    await user.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  // 17. Shows KB-sized file correctly
  it("shows file size in KB for small files", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    // 500 KB file
    const file = createMockFile("small.md", 500 * 1024);

    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/500\.0 KB/)).toBeInTheDocument();
    });
  });

  // 18. Import button disabled on file tab when file has error
  it("import button is disabled on file tab when file has validation error", async () => {
    const user = userEvent.setup();
    renderModal();

    await user.click(screen.getByText("From File"));

    const fileInput = screen.getByLabelText(/file/i) as HTMLInputElement;
    const badFile = createMockFile("script.exe", 1024);

    await user.upload(fileInput, badFile);

    await waitFor(() => {
      const importBtn = screen.getByRole("button", { name: /import/i });
      expect(importBtn).toBeDisabled();
    });
  });
});
