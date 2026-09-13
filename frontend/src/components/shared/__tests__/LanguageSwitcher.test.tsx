import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageSwitcher } from "../LanguageSwitcher";

/**
 * The trigger is a Radix DropdownMenu, which opens on `pointerdown` — a bare
 * `fireEvent.click` never opened it, so these assertions used to read a closed
 * menu. `userEvent` fires the full pointer sequence.
 *
 * Queries for a locale name are scoped to the menu: the trigger button also
 * renders the current locale's name, so an unscoped `getByText("English")`
 * matches twice once the menu is open.
 */
async function openMenu() {
  const user = userEvent.setup();
  const trigger = screen.getByLabelText("Select language");
  await user.click(trigger);
  return { user, menu: await screen.findByRole("menu") };
}

describe("LanguageSwitcher", () => {
  it("should render with default locale (en)", () => {
    render(<LanguageSwitcher />);
    expect(screen.getByLabelText("Select language")).toBeInTheDocument();
  });

  it("should show current locale name in non-compact mode", () => {
    render(<LanguageSwitcher currentLocale="en" />);
    const button = screen.getByLabelText("Select language");
    expect(button).toHaveTextContent("English");
  });

  it("should show only icon in compact mode", () => {
    render(<LanguageSwitcher compact />);
    const button = screen.getByLabelText("Select language");
    expect(button).toBeInTheDocument();
    expect(screen.queryByText("English")).not.toBeInTheDocument();
  });

  it("should open dropdown when clicked", async () => {
    render(<LanguageSwitcher />);
    const { menu } = await openMenu();

    expect(within(menu).getByText("English")).toBeInTheDocument();
    expect(within(menu).getByText("Español")).toBeInTheDocument();
    expect(within(menu).getByText("Deutsch")).toBeInTheDocument();
  });

  it("should highlight current locale with checkmark", async () => {
    render(<LanguageSwitcher currentLocale="es" />);
    const { menu } = await openMenu();

    const selectedItem = within(menu)
      .getByText("Español")
      .closest("[role='menuitem']");
    expect(selectedItem).toBeInTheDocument();
    expect(within(selectedItem as HTMLElement).getByLabelText("Selected")).toBeInTheDocument();
  });

  it("should call onLocaleChange when a locale is selected", async () => {
    const handleLocaleChange = jest.fn();
    render(<LanguageSwitcher onLocaleChange={handleLocaleChange} />);

    const { user, menu } = await openMenu();
    await user.click(within(menu).getByText("Español"));

    expect(handleLocaleChange).toHaveBeenCalledWith("es");
  });

  it("should set the NEXT_LOCALE cookie when onLocaleChange is not provided", async () => {
    render(<LanguageSwitcher />);

    const { user, menu } = await openMenu();
    await user.click(within(menu).getByText("Deutsch"));

    expect(document.cookie).toContain("NEXT_LOCALE=de");
  });

  it("should display one menu item per locale", async () => {
    render(<LanguageSwitcher />);
    await openMenu();

    expect(screen.getAllByRole("menuitem")).toHaveLength(3); // en, es, de
  });

  it("should apply custom className to trigger button", () => {
    render(<LanguageSwitcher className="custom-class" />);
    const button = screen.getByLabelText("Select language");
    expect(button).toHaveClass("custom-class");
  });

  it("should be keyboard accessible", async () => {
    const user = userEvent.setup();
    render(<LanguageSwitcher />);
    const trigger = screen.getByLabelText("Select language");

    trigger.focus();
    expect(trigger).toHaveFocus();

    await user.keyboard("{Enter}");

    const menu = await screen.findByRole("menu");
    expect(within(menu).getByText("English")).toBeInTheDocument();
  });
});
