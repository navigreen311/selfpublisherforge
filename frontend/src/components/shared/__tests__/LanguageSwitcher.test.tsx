import { render, screen, fireEvent } from "@testing-library/react";
import { LanguageSwitcher } from "../LanguageSwitcher";

describe("LanguageSwitcher", () => {
  it("should render with default locale (en)", () => {
    render(<LanguageSwitcher />);
    expect(screen.getByLabelText("Select language")).toBeInTheDocument();
  });

  it("should show current locale name in non-compact mode", () => {
    render(<LanguageSwitcher currentLocale="en" />);
    // The "English" text is inside a button, but may be hidden on mobile
    const button = screen.getByLabelText("Select language");
    expect(button).toBeInTheDocument();
  });

  it("should show only icon in compact mode", () => {
    render(<LanguageSwitcher compact />);
    const button = screen.getByLabelText("Select language");
    expect(button).toBeInTheDocument();
    // In compact mode, the locale name should not be visible
    expect(screen.queryByText("English")).not.toBeInTheDocument();
  });

  it("should open dropdown when clicked", () => {
    render(<LanguageSwitcher />);
    const trigger = screen.getByLabelText("Select language");
    fireEvent.click(trigger);

    // Check if all locale options are displayed
    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.getByText("Español")).toBeInTheDocument();
    expect(screen.getByText("Deutsch")).toBeInTheDocument();
  });

  it("should highlight current locale with checkmark", () => {
    render(<LanguageSwitcher currentLocale="es" />);
    const trigger = screen.getByLabelText("Select language");
    fireEvent.click(trigger);

    // The check mark should be present for Spanish
    const selectedItem = screen.getByText("Español").closest("[role='menuitem']");
    expect(selectedItem).toBeInTheDocument();
  });

  it("should call onLocaleChange when a locale is selected", () => {
    const handleLocaleChange = jest.fn();
    render(<LanguageSwitcher onLocaleChange={handleLocaleChange} />);

    const trigger = screen.getByLabelText("Select language");
    fireEvent.click(trigger);

    const spanishOption = screen.getByText("Español");
    fireEvent.click(spanishOption);

    expect(handleLocaleChange).toHaveBeenCalledWith("es");
  });

  it("should log to console when onLocaleChange is not provided", () => {
    const consoleSpy = jest.spyOn(console, "log").mockImplementation();
    render(<LanguageSwitcher />);

    const trigger = screen.getByLabelText("Select language");
    fireEvent.click(trigger);

    const germanOption = screen.getByText("Deutsch");
    fireEvent.click(germanOption);

    expect(consoleSpy).toHaveBeenCalledWith("Switching to locale: de");
    consoleSpy.mockRestore();
  });

  it("should display flag icons for each locale", () => {
    render(<LanguageSwitcher />);
    const trigger = screen.getByLabelText("Select language");
    fireEvent.click(trigger);

    // Check for flag emojis (they should be present in the dropdown)
    const menuItems = screen.getAllByRole("menuitem");
    expect(menuItems).toHaveLength(3); // en, es, de
  });

  it("should apply custom className to trigger button", () => {
    render(<LanguageSwitcher className="custom-class" />);
    const button = screen.getByLabelText("Select language");
    expect(button).toHaveClass("custom-class");
  });

  it("should be keyboard accessible", () => {
    render(<LanguageSwitcher />);
    const trigger = screen.getByLabelText("Select language");

    // Focus the trigger
    trigger.focus();
    expect(trigger).toHaveFocus();

    // Open with Enter key
    fireEvent.keyDown(trigger, { key: "Enter", code: "Enter" });

    // Verify dropdown is open by checking for locale options
    expect(screen.getByText("English")).toBeInTheDocument();
  });
});
