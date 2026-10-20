/* Production-browser integration and accessibility tests by Jason Stys.
 * Functions: load, choose and cross-engine test cases. Variables: real downloads, faults and replay.
 * Exact declaration/variable inventory: docs/CODE_INDEX.md. Runs against the actual Python service.
 */
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

/** Wait for actual native evidence rather than mocking a successful default render. */
async function scrub(page: Page, tick: number): Promise<void> {
  /** Set a native range and dispatch its real input contract. */
  await page.getByLabel("Replay tick").evaluate((input: HTMLInputElement, value) => {
    input.value = String(value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }, tick);
}
/** Wait for the experiment's named status, not the implicit status role of output. */
async function load(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText("Complete");
}
/** Submit a finite fixture using the same controls as a user. */
async function choose(page: Page, scenario: string): Promise<void> {
  await page.getByLabel("Fault scenario").selectOption(scenario);
  await page.getByRole("button", { name: "Run experiment" }).click();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
    `deterministic ${scenario} replay`,
  );
}
test("real native defaults, recovery and defaults reset", async ({ page }) => {
  await load(page);
  await expect(page.locator("#sensor")).toHaveText("Unavailable");
  await choose(page, "watchdog-hang");
  await scrub(page, 124);
  await expect(page.locator("#mode")).toHaveText("BOOT");
  await expect(page.locator("#boot")).toContainText("Boot 2");
  await scrub(page, 126);
  await expect(page.locator("#mode")).toHaveText("SAFE");
  await page.getByRole("button", { name: "Defaults" }).click();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
    "deterministic nominal replay",
  );
});
test("missing ground frames are not zeros and chart segments remain separated", async ({
  page,
}) => {
  await load(page);
  await choose(page, "telemetry-gap");
  await page.getByLabel("Perspective").selectOption("ground");
  await scrub(page, 125);
  await expect(page.locator("#mode")).toHaveText("Unavailable");
  await expect(page.locator("#payloads")).toHaveText("Unavailable");
  await expect(page.locator("#frame-state")).toHaveText("NO DOWNLINK FRAME");
  await expect(page.locator('path[data-series="payloads"]')).toHaveCount(3);
  await page.getByLabel("Perspective").selectOption("truth");
  await expect(page.locator("#mode")).toHaveText("SCIENCE");
  await expect(page.locator('path[data-series="payloads"]')).toHaveCount(2);
});
test("real JSON CSV and inert HTML download bodies", async ({ page }) => {
  await load(page);
  await choose(page, "checkpoint-corrupt");
  for (const format of ["json", "csv", "html"]) {
    const pending = page.waitForEvent("download");
    await page.locator(`#download-${format}`).click();
    const download = await pending;
    const path = await download.path();
    expect(path).not.toBeNull();
    const body = await readFile(path!, "utf8");
    expect(download.suggestedFilename()).toContain(`.${format}`);
    if (format === "json") expect(JSON.parse(body).summary.resets).toBe(1);
    if (format === "csv") {
      expect(body).toContain("sensor_valid");
      expect(body.split("\n")).toHaveLength(484);
    }
    if (format === "html") {
      expect(body).toContain("Content-Security-Policy");
      expect(body).not.toContain("<script");
    }
  }
});
test("failure clears stale evidence and retry recovers", async ({ page }) => {
  await load(page);
  await page.route("**/api/run?**", (route) => route.fulfill({ status: 503, body: "unavailable" }));
  await chooseFailure();
  await expect(page.locator("#results")).toBeHidden();
  await page.unroute("**/api/run?**");
  await page.getByRole("button", { name: "Retry experiment" }).click();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText("Complete");
  /** Trigger expected failure without waiting for a successful native status. */
  async function chooseFailure(): Promise<void> {
    await page.getByRole("button", { name: "Run experiment" }).click();
    await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
      "Experiment failed",
    );
  }
});
test("rapid playback toggles cannot leak animation owners", async ({ page }) => {
  await page.clock.install();
  await load(page);
  for (let index = 0; index < 4; index++) {
    await page.getByRole("button", { name: "Play replay", exact: true }).click();
    await page.getByRole("button", { name: "Pause replay", exact: true }).click();
  }
  const before = await page.locator("#tick-label").innerText();
  await page.clock.runFor(800);
  expect(await page.locator("#tick-label").innerText()).toBe(before);
  await page.getByRole("button", { name: "Play replay", exact: true }).click();
  await page.clock.runFor(700);
  await expect(page.locator("#tick-label")).not.toHaveText(before);
  await page.getByRole("button", { name: "Pause replay", exact: true }).click();
});
test("optional blocked storage and mobile WCAG scan", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("blocked", "SecurityError");
      },
    });
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await load(page);
  const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(scan.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.getByLabel("Fault scenario").selectOption("sensor-stale");
  await page.getByRole("button", { name: "Run experiment" }).click();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
    "deterministic sensor-stale replay",
  );
});
test("preference restoration, periodic ledger and constrained API", async ({ page, request }) => {
  await load(page);
  await choose(page, "brownout");
  await page.reload();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
    "deterministic brownout replay",
  );
  await expect(page.locator("#events")).not.toContainText("checkpoint saved");
  await page.getByLabel("Include periodic saves").check();
  await expect(page.locator("#events")).toContainText("checkpoint saved");
  expect((await request.get("/api/run?watchdog=0")).status()).toBe(400);
  expect(
    (await request.get("/api/run", { headers: { Origin: "https://evil.example" } })).status(),
  ).toBe(403);
});
