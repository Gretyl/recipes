import { describe, it, expect, beforeEach } from "vitest";
import { loadArtifact } from "../../../shared/harness/load-artifact";

describe("hello-artifact", () => {
  let mounted: Awaited<ReturnType<typeof loadArtifact>>;

  beforeEach(async () => {
    mounted = await loadArtifact("hello-artifact");
  });

  it("starts the counter at zero", () => {
    const display = mounted.document.getElementById("count-display");
    expect(display?.textContent ?? display?.getAttribute("value")).toBe("0");
  });

  it("increments the counter on click", () => {
    const button = mounted.document.getElementById(
      "count-btn",
    ) as HTMLButtonElement;
    button.click();
    button.click();
    button.click();
    const display = mounted.document.getElementById(
      "count-display",
    ) as HTMLOutputElement;
    expect(display.value).toBe("3");
  });

  it("persists the counter through window.storage", () => {
    const button = mounted.document.getElementById(
      "count-btn",
    ) as HTMLButtonElement;
    button.click();
    button.click();
    expect(mounted.storage.getItem("hello-artifact:count")).toBe("2");
  });
});
