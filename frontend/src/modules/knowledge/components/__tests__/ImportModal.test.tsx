import React from "react";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { render } from "@/test-utils";
import { ImportModal } from "../ImportModal";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockImportAsync = jest.fn().mockResolvedValue({ title: "Imported doc" });
const mockCreateAsync = jest.fn().mockResolvedValue({ title: "Pasted content" });

jest.mock("../../hooks", () => ({
  useImportEntry: () => ({
    mutateAsync: mockImportAsync,
    isPending: false,
    isError: false,
  }),
  useCreateEntry: () => ({
    mutate: jest.fn(),
    mutateAsync: mockCreateAsync,
    isPending: false,
    isError: false,
    error: null,
    reset: jest.fn(),
  }),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderModal(props: Partial<React.ComponentProps<typeof ImportModal>> = {}) {
  const defaultProps: React.ComponentProps<typeof ImportModal> = {
    open: true,
    onClose: jest.fn(),
    ...props,
  };
  return { ...render(<ImportModal {...defaultProps} />), props: defaultProps };
}

/** The modal opens on a chooser; each option swaps in its own pane. */
async function openPane(label: string) {
  const user = userEvent.setup();
  await user.click(screen.getByText(label));
  return user;
}

/**
 * The file input is hidden behind the drop zone, so drive it directly. The
 * dialog renders through a portal, so it is not under the render container.
 */
function fileInput(): HTMLInputElement {
  const input = document.body.querySelector("input[type=file]");
  if (!input) throw new Error("file input not found");
  return input as HTMLInputElement;
}

function makeFile(name: string, size: number): File {
  const file = new File(["x"], name, { type: "application/octet-stream" });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ImportModal", () => {
  it("renders every import option when open", () => {
    renderModal();

    expect(screen.getByText("Import Research")).toBeInTheDocument();
    expect(screen.getByText("Upload Files")).toBeInTheDocument();
    expect(screen.getByText("Import from URL")).toBeInTheDocument();
    expect(screen.getByText("Paste Clipboard")).toBeInTheDocument();
    expect(screen.getByText("From Manuscript")).toBeInTheDocument();
  });

  it("does not render anything when open is false", () => {
    renderModal({ open: false });
    expect(screen.queryByText("Import Research")).not.toBeInTheDocument();
  });

  it("opens a pane and returns to the chooser", async () => {
    renderModal();
    const user = await openPane("Upload Files");

    expect(screen.getByText("Drop a file here or click to browse")).toBeInTheDocument();
    expect(screen.queryByText("Paste Clipboard")).not.toBeInTheDocument();

    await user.click(screen.getByText("Back to options"));
    expect(screen.getByText("Paste Clipboard")).toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", async () => {
    const { props } = renderModal();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /close/i }));

    expect(props.onClose).toHaveBeenCalled();
  });

  describe("file upload", () => {
    it("shows the accepted formats and size limit as a hint", async () => {
      renderModal();
      await openPane("Upload Files");

      expect(
        screen.getByText("DOCX, PDF, TXT, MD, EPUB (max 50.0 MB)")
      ).toBeInTheDocument();
    });

    it("rejects an unsupported format", async () => {
      renderModal();
      await openPane("Upload Files");

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("malware.exe", 1024)] },
      });

      expect(
        await screen.findByText("Unsupported format. Accepted: DOCX, PDF, TXT, MD, EPUB")
      ).toBeInTheDocument();
    });

    it("rejects a file over 50MB", async () => {
      renderModal();
      await openPane("Upload Files");

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("huge.pdf", 51 * 1024 * 1024)] },
      });

      expect(
        await screen.findByText("File too large (51.0 MB). Max 50.0 MB.")
      ).toBeInTheDocument();
    });

    it.each([".pdf", ".epub", ".txt", ".md", ".docx"])("accepts %s", async (ext) => {
      renderModal();
      await openPane("Upload Files");

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("notes" + ext, 2048)] },
      });

      expect(await screen.findByText("notes" + ext)).toBeInTheDocument();
      expect(screen.queryByText(/Unsupported format/)).not.toBeInTheDocument();
    });

    it("shows the file size in KB for small files", async () => {
      renderModal();
      await openPane("Upload Files");

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("small.txt", 2048)] },
      });

      expect(await screen.findByText("(2.0 KB)")).toBeInTheDocument();
    });

    it("shows the file size in MB for large files", async () => {
      renderModal();
      await openPane("Upload Files");

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("big.pdf", 3 * 1024 * 1024)] },
      });

      expect(await screen.findByText("(3.0 MB)")).toBeInTheDocument();
    });

    it("keeps the import button disabled until a valid file is read", async () => {
      renderModal();
      await openPane("Upload Files");

      const importButton = screen.getByRole("button", { name: /import file/i });
      expect(importButton).toBeDisabled();

      fireEvent.change(fileInput(), {
        target: { files: [makeFile("bad.exe", 1024)] },
      });
      await screen.findByText(/Unsupported format/);
      expect(importButton).toBeDisabled();
    });
  });

  describe("url import", () => {
    it("shows an error for a URL with no protocol", async () => {
      renderModal();
      const user = await openPane("Import from URL");

      const input = screen.getByLabelText("URL");
      await user.type(input, "example.com/article");
      fireEvent.blur(input);

      expect(
        await screen.findByText("URL must start with http:// or https://")
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /import url/i })).toBeDisabled();
    });

    it("accepts an https URL and submits it", async () => {
      renderModal();
      const user = await openPane("Import from URL");

      await user.type(screen.getByLabelText("URL"), "https://example.com/article");

      const importButton = screen.getByRole("button", { name: /import url/i });
      expect(importButton).toBeEnabled();

      await user.click(importButton);

      await waitFor(() =>
        expect(mockImportAsync).toHaveBeenCalledWith({
          url: "https://example.com/article",
        })
      );
    });
  });

  describe("clipboard", () => {
    it("saves pasted text to the knowledge base", async () => {
      renderModal();
      const user = await openPane("Paste Clipboard");

      const textarea = screen.getByLabelText("Paste your content");
      expect(
        screen.getByRole("button", { name: /save to knowledge base/i })
      ).toBeDisabled();

      await user.type(textarea, "A useful note");
      await user.click(screen.getByRole("button", { name: /save to knowledge base/i }));

      await waitFor(() =>
        expect(mockCreateAsync).toHaveBeenCalledWith({
          title: "Pasted content",
          content: "A useful note",
          source_type: "clip",
        })
      );
    });
  });
});
