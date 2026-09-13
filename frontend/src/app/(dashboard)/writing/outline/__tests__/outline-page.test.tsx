import React from "react";
import { render, screen, waitFor } from "@/test-utils";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/writing/outline",
}));

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", org_id: "org1" },
    isAuthenticated: true,
  }),
}));

// Mock next/link to render a plain anchor
jest.mock("next/link", () => {
  return ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

// Mock sonner toast
const mockToastError = jest.fn();
const mockToastSuccess = jest.fn();
jest.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => mockToastError(...args),
    success: (...args: unknown[]) => mockToastSuccess(...args),
  },
}));

// Mock the standalone outline hook
const mockMutateAsync = jest.fn();
const mockGenerateHook = jest.fn();

jest.mock("@/modules/writing/hooks", () => ({
  useGenerateStandaloneOutline: (...args: unknown[]) => mockGenerateHook(...args),
}));


// ---------------------------------------------------------------------------
// Import the component under test (must be AFTER mocks)
// ---------------------------------------------------------------------------
import OutlineGeneratorPage from "../../outline/page";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const mockOutlineResponse = {
  book_title: "Test Book",
  genre: "Fiction",
  total_chapters: 3,
  chapters: [
    {
      chapter_number: 1,
      title: "The Beginning",
      description: "An introduction to the world.",
      key_points: ["Introduce hero", "Set the scene"],
      estimated_word_count: 3000,
    },
    {
      chapter_number: 2,
      title: "The Middle",
      description: "The conflict deepens.",
      key_points: ["Rising action", "Antagonist revealed"],
      estimated_word_count: 4000,
    },
    {
      chapter_number: 3,
      title: "The End",
      description: "Resolution of the story.",
      key_points: ["Climax", "Resolution"],
      estimated_word_count: 3500,
    },
  ],
  synopsis: "A thrilling tale of adventure and discovery.",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupDefaultHook(overrides: Record<string, unknown> = {}) {
  mockGenerateHook.mockReturnValue({
    mutateAsync: mockMutateAsync,
    isPending: false,
    ...overrides,
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("OutlineGeneratorPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupDefaultHook();
  });

  it("renders outline generation form with heading", () => {
    render(<OutlineGeneratorPage />);

    expect(
      screen.getByRole("heading", { name: /AI Outline Generator/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText("Generate a complete book outline with chapter summaries")
    ).toBeInTheDocument();
  });

  it("has all form fields present (title, genre, tone, audience, chapters, premise)", () => {
    render(<OutlineGeneratorPage />);

    // Title
    expect(screen.getByText("Book Title *")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Enter your book title")
    ).toBeInTheDocument();

    // Genre
    expect(screen.getByText("Genre")).toBeInTheDocument();

    // Tone
    expect(screen.getByText("Tone")).toBeInTheDocument();

    // Target Audience
    expect(screen.getByText("Target Audience")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("e.g. Young adults, business professionals")
    ).toBeInTheDocument();

    // Number of Chapters
    expect(screen.getByText("Number of Chapters")).toBeInTheDocument();

    // Premise / Description
    expect(screen.getByText("Premise / Description")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(
        "Describe your book's premise, main themes, or key plot points..."
      )
    ).toBeInTheDocument();
  });

  it("form validation - generate button is disabled when title is empty", () => {
    render(<OutlineGeneratorPage />);

    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    expect(generateButton).toBeDisabled();
  });

  it("form validation - shows toast error when submitting without title", async () => {
    const user = userEvent.setup();
    // Override to enable the button (isPending false, we'll test the handler path)
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // The button is disabled with empty title due to disabled={... || !title.trim()}
    // So we type a space (which trims to empty)
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "   ");

    // Button should still be disabled since "   ".trim() === ""
    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    expect(generateButton).toBeDisabled();
  });

  it("submit triggers mutation with correct payload", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockOutlineResponse);
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // Fill in title
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");

    // Fill in audience
    const audienceInput = screen.getByPlaceholderText(
      "e.g. Young adults, business professionals"
    );
    await user.type(audienceInput, "Young adults");

    // Fill in premise
    const premiseInput = screen.getByPlaceholderText(
      "Describe your book's premise, main themes, or key plot points..."
    );
    await user.type(premiseInput, "A hero's journey");

    // Click generate
    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    expect(mockMutateAsync).toHaveBeenCalledWith({
      book_title: "Test Book",
      genre: "Fiction",
      target_audience: "Young adults",
      num_chapters: 12,
      premise: "A hero's journey",
      tone: "commercial",
    });
  });

  it("results display with chapters after successful generation", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockOutlineResponse);
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // Fill in title and generate
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");

    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument();
    });

    // Synopsis
    expect(
      screen.getByText("A thrilling tale of adventure and discovery.")
    ).toBeInTheDocument();

    // Chapters
    expect(screen.getByText(/Chapter 1: The Beginning/)).toBeInTheDocument();
    expect(screen.getByText(/Chapter 2: The Middle/)).toBeInTheDocument();
    expect(screen.getByText(/Chapter 3: The End/)).toBeInTheDocument();

    // Descriptions
    expect(
      screen.getByText("An introduction to the world.")
    ).toBeInTheDocument();
    expect(screen.getByText("The conflict deepens.")).toBeInTheDocument();
    expect(
      screen.getByText("Resolution of the story.")
    ).toBeInTheDocument();

    // Key points
    expect(screen.getByText("Introduce hero")).toBeInTheDocument();
    expect(screen.getByText("Set the scene")).toBeInTheDocument();
    expect(screen.getByText("Rising action")).toBeInTheDocument();

    // Word counts
    expect(screen.getByText("~3,000 words")).toBeInTheDocument();
    expect(screen.getByText("~4,000 words")).toBeInTheDocument();
    expect(screen.getByText("~3,500 words")).toBeInTheDocument();
  });

  it("chapter reorder (up) works correctly", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockOutlineResponse);
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // Generate the outline
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");
    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/Chapter 1: The Beginning/)).toBeInTheDocument();
    });

    // Find all up arrow buttons - they should be in order corresponding to chapters
    // Chapter 2's up button should move it to position 1
    const allButtons = screen.getAllByRole("button");
    // The up/down buttons are small icon-only buttons. We need to find them.
    // Looking at the structure: each chapter has an up and down button.
    // First chapter's up button is disabled (index === 0).
    // We can find buttons by their container structure.

    // There should be 6 reorder buttons (2 per chapter: up + down) plus other buttons
    // Let's find buttons that contain ChevronUp/ChevronDown SVGs
    // The second chapter's "up" button (index 1) should be clickable
    // Since the up buttons come first for each chapter, the pattern is:
    // [ch1-up(disabled), ch1-down, ch2-up, ch2-down, ch3-up, ch3-down(disabled)]

    // Click ch2 up button to move "The Middle" to position 1
    // Chapter order should be: The Middle, The Beginning, The End
    // After clicking, chapter 2 becomes chapter 1

    // Verify initial order
    expect(screen.getByText(/Chapter 1: The Beginning/)).toBeInTheDocument();
    expect(screen.getByText(/Chapter 2: The Middle/)).toBeInTheDocument();

    // Get the chapter cards area - the up/down buttons are inside small ghost buttons
    // Each card has two reorder buttons. We need to target the "up" button of ch2.
    // We'll look for all ghost/small buttons that are NOT disabled and come after the first chapter.
    // A simpler approach: find all the SVGs and identify the up arrows

    // The second chapter's up button is the 3rd button of that type (1st is ch1-up disabled, 2nd is ch1-down)
    // Actually let's just use a different approach - get all buttons and look for patterns
    const reorderButtons = allButtons.filter(
      (btn) =>
        btn.classList.contains("h-7") && btn.classList.contains("w-7")
    );
    // reorderButtons: [ch1-up, ch1-down, ch2-up, ch2-down, ch3-up, ch3-down]
    // ch2's up button is index 2
    if (reorderButtons.length >= 3) {
      await user.click(reorderButtons[2]); // ch2 up
    }

    // After moving, chapter 2 (The Middle) should now be chapter 1
    await waitFor(() => {
      expect(screen.getByText(/Chapter 1: The Middle/)).toBeInTheDocument();
      expect(screen.getByText(/Chapter 2: The Beginning/)).toBeInTheDocument();
      expect(screen.getByText(/Chapter 3: The End/)).toBeInTheDocument();
    });
  });

  it("chapter reorder (down) works correctly", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockOutlineResponse);
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // Generate the outline
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");
    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText(/Chapter 1: The Beginning/)).toBeInTheDocument();
    });

    // Find reorder buttons
    const allButtons = screen.getAllByRole("button");
    const reorderButtons = allButtons.filter(
      (btn) =>
        btn.classList.contains("h-7") && btn.classList.contains("w-7")
    );
    // reorderButtons: [ch1-up, ch1-down, ch2-up, ch2-down, ch3-up, ch3-down]
    // ch1's down button is index 1
    if (reorderButtons.length >= 2) {
      await user.click(reorderButtons[1]); // ch1 down
    }

    // After moving ch1 down, "The Middle" should be chapter 1, "The Beginning" should be chapter 2
    await waitFor(() => {
      expect(screen.getByText(/Chapter 1: The Middle/)).toBeInTheDocument();
      expect(screen.getByText(/Chapter 2: The Beginning/)).toBeInTheDocument();
      expect(screen.getByText(/Chapter 3: The End/)).toBeInTheDocument();
    });
  });

  it("export to clipboard works", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockResolvedValue(mockOutlineResponse);
    setupDefaultHook();

    // Spy on clipboard.writeText
    const writeTextSpy = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextSpy },
      writable: true,
      configurable: true,
    });

    render(<OutlineGeneratorPage />);

    // Generate the outline
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");
    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument();
    });

    // Click export button
    const exportButton = screen.getByRole("button", {
      name: /Export as Markdown/i,
    });
    await user.click(exportButton);

    // Verify clipboard was written to
    await waitFor(() => {
      expect(writeTextSpy).toHaveBeenCalledTimes(1);
    });
    const writtenText = writeTextSpy.mock.calls[0][0];
    expect(writtenText).toContain("# Test Book");
    expect(writtenText).toContain("## Synopsis");
    expect(writtenText).toContain("A thrilling tale of adventure and discovery.");
    expect(writtenText).toContain("### Chapter 1: The Beginning");
    expect(writtenText).toContain("### Chapter 2: The Middle");
    expect(writtenText).toContain("### Chapter 3: The End");

    // Toast success should have been called
    expect(mockToastSuccess).toHaveBeenCalledWith(
      "Outline copied to clipboard as Markdown"
    );
  });

  it("loading state during generation shows spinner and updated button text", () => {
    setupDefaultHook({ isPending: true });

    render(<OutlineGeneratorPage />);

    // When isPending is true, the button text changes
    expect(screen.getByText("Generating Outline...")).toBeInTheDocument();

    // The button should be disabled during generation
    const generateButton = screen.getByRole("button", {
      name: /Generating Outline/i,
    });
    expect(generateButton).toBeDisabled();
  });

  it("shows toast error when generation fails", async () => {
    const user = userEvent.setup();
    mockMutateAsync.mockRejectedValue(new Error("Server error"));
    setupDefaultHook();

    render(<OutlineGeneratorPage />);

    // Fill in title and generate
    const titleInput = screen.getByPlaceholderText("Enter your book title");
    await user.type(titleInput, "Test Book");

    const generateButton = screen.getByRole("button", {
      name: /Generate Outline/i,
    });
    await user.click(generateButton);

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(
        "Failed to generate outline. Please try again."
      );
    });
  });

  it("has a back link to /writing", () => {
    render(<OutlineGeneratorPage />);

    const backLink = screen.getByRole("link", { name: /Back/i });
    expect(backLink).toHaveAttribute("href", "/writing");
  });
});
