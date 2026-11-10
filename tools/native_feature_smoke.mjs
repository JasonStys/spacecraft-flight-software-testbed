/**
 * File: native_feature_smoke.mjs
 * Purpose: Jason Stys — actual packaged recovery-observability UI and exported report acceptance.
 * Functions: runNativeJourney callback; variables: page, downloaded bytes and native evidence.
 * Exact source locations: docs/CODE_INDEX.md. Synthetic watchdog fixture only, no flight hardware.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request, outputDirectory, version }) => {
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText("Complete");
  await page.getByLabel("Fault scenario").selectOption("watchdog-hang");
  await page.getByRole("button", { name: "Run experiment" }).click();
  await expect(page.getByRole("status", { name: "Experiment status" })).toContainText(
    "deterministic watchdog-hang replay",
  );
  await expect(page.locator("#observability")).toContainText("boot: 1 → 2");
  await expect(page.locator("#observability")).toContainText("received confirmation");
  await page.getByLabel("Perspective").selectOption("ground");
  await expect(page.locator("#observability")).toContainText("independent of the replay cursor");
  const response = await request.get("api/run?scenario=watchdog-hang");
  assert.equal(response.status(), 200);
  const evidence = await response.json();
  assert.equal(evidence.provenance.version, version);
  assert.equal(evidence.summary.resets, 1);
  const boot = evidence.observability.find((row) => row.field === "boot" && row.after === 2);
  assert.ok(boot && boot.received_confirmation_tick >= boot.onboard_tick);
  const pending = page.waitForEvent("download");
  await page.locator("#download-json").click();
  const download = await pending;
  assert.equal(download.suggestedFilename(), "flight-evidence.json");
  const destination = path.join(outputDirectory, "native-user-export.json");
  await download.saveAs(destination);
  assert.deepEqual(JSON.parse(await readFile(destination, "utf8")), evidence);
  assert.equal((await request.get("api/run?watchdog=0")).status(), 400);
});
