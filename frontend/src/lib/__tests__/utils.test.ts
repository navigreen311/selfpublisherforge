import { cn } from "../utils";

describe("cn utility", () => {
  it("merges class names", () => {
    const result = cn("px-4", "py-2");
    expect(result).toBe("px-4 py-2");
  });

  it("handles conditional classes via clsx", () => {
    const isActive = true;
    const result = cn("base", isActive && "active");
    expect(result).toBe("base active");
  });

  it("removes falsy values", () => {
    const result = cn("base", false, null, undefined, "end");
    expect(result).toBe("base end");
  });

  it("merges conflicting tailwind classes (last wins)", () => {
    // tailwind-merge should resolve px-4 and px-2 to just px-2
    const result = cn("px-4", "px-2");
    expect(result).toBe("px-2");
  });

  it("merges conflicting tailwind bg classes", () => {
    const result = cn("bg-red-500", "bg-blue-500");
    expect(result).toBe("bg-blue-500");
  });

  it("handles empty input", () => {
    const result = cn();
    expect(result).toBe("");
  });

  it("handles arrays of class names", () => {
    const result = cn(["foo", "bar"], "baz");
    expect(result).toBe("foo bar baz");
  });

  it("deduplicates identical classes", () => {
    const result = cn("p-4", "p-4");
    expect(result).toBe("p-4");
  });
});
