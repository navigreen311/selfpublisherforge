import {
  locales,
  defaultLocale,
  localeNames,
  localeFlags,
  isValidLocale,
  getLocaleFromNavigator,
} from "../config";

describe("i18n Config", () => {
  describe("locales", () => {
    it("should include en, es, and de", () => {
      expect(locales).toEqual(["en", "es", "de"]);
    });

    it("should be readonly", () => {
      expect(Object.isFrozen(locales)).toBe(false); // readonly is compile-time only
      expect(Array.isArray(locales)).toBe(true);
    });
  });

  describe("defaultLocale", () => {
    it("should be en", () => {
      expect(defaultLocale).toBe("en");
    });
  });

  describe("localeNames", () => {
    it("should have names for all locales", () => {
      expect(localeNames.en).toBe("English");
      expect(localeNames.es).toBe("Español");
      expect(localeNames.de).toBe("Deutsch");
    });
  });

  describe("localeFlags", () => {
    it("should have flags for all locales", () => {
      expect(localeFlags.en).toBe("🇺🇸");
      expect(localeFlags.es).toBe("🇪🇸");
      expect(localeFlags.de).toBe("🇩🇪");
    });
  });

  describe("isValidLocale", () => {
    it("should return true for valid locales", () => {
      expect(isValidLocale("en")).toBe(true);
      expect(isValidLocale("es")).toBe(true);
      expect(isValidLocale("de")).toBe(true);
    });

    it("should return false for invalid locales", () => {
      expect(isValidLocale("fr")).toBe(false);
      expect(isValidLocale("it")).toBe(false);
      expect(isValidLocale("")).toBe(false);
      expect(isValidLocale("invalid")).toBe(false);
    });
  });

  describe("getLocaleFromNavigator", () => {
    const originalWindow = global.window;

    afterEach(() => {
      global.window = originalWindow;
    });

    it("should return default locale when window is undefined (SSR)", () => {
      // @ts-expect-error - Testing server-side rendering
      delete global.window;
      expect(getLocaleFromNavigator()).toBe(defaultLocale);
    });

    it("should return locale from browser language", () => {
      Object.defineProperty(window.navigator, "language", {
        writable: true,
        configurable: true,
        value: "es-ES",
      });
      expect(getLocaleFromNavigator()).toBe("es");
    });

    it("should return default locale for unsupported browser language", () => {
      Object.defineProperty(window.navigator, "language", {
        writable: true,
        configurable: true,
        value: "fr-FR",
      });
      expect(getLocaleFromNavigator()).toBe(defaultLocale);
    });

    it("should handle language code without region", () => {
      Object.defineProperty(window.navigator, "language", {
        writable: true,
        configurable: true,
        value: "de",
      });
      expect(getLocaleFromNavigator()).toBe("de");
    });
  });
});
