import { test, expect } from "@playwright/test";

test.describe("hello-artifact (deployed)", () => {
  test("renders the counter at zero", async ({ page }) => {
    await page.goto("/hello-artifact.html");
    await expect(page.locator("#count-display")).toHaveText("0");
  });

  test("increments on click", async ({ page }) => {
    await page.goto("/hello-artifact.html");
    const button = page.locator("#count-btn");
    await button.click();
    await button.click();
    await expect(page.locator("#count-display")).toHaveText("2");
  });
});
