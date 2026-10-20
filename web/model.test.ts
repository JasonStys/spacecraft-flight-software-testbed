/* Pure rendering and preference contracts by Jason Stys.
 * Functions: Vitest contracts. Variables: synthetic rows, poisoned preferences, finite catalog.
 * Source/function inventory: docs/CODE_INDEX.md. Tests do not contact external services.
 */
import { describe, expect, it } from "vitest";
import { format, observed, paths, preferences } from "./model";
import type { Catalog, Sample } from "./types";

const row = { tick: 0, payloads: 0, committed: 0, delivered: true } as Sample;
const defaults = {
  scenario: "nominal",
  duration: 240,
  fault_tick: 120,
  watchdog: 5,
  checkpoint_period: 8,
  sample_period: 2,
};
const catalog: Catalog = {
  defaults,
  scenarios: { nominal: "Healthy", "telemetry-gap": "Missing" },
  choices: { duration: [240, 480], watchdog: [3, 5, 8] },
};
describe("finite preferences", () => {
  for (const raw of [
    null,
    "{",
    "[]",
    "null",
    "false",
    '"text"',
    '{"__proto__":{"x":1},"constructor":2,"toString":3,"scenario":"toString"}',
  ]) {
    it(`ignores malformed and inherited keys ${raw}`, () =>
      expect(preferences(raw, catalog)).toEqual(defaults));
  }
  it("accepts only reviewed primitive choices", () =>
    expect(
      preferences(
        '{"scenario":"telemetry-gap","duration":480,"watchdog":true,"unknown":1}',
        catalog,
      ),
    ).toEqual({ ...defaults, scenario: "telemetry-gap", duration: 480 }));
});
describe("truthful charts", () => {
  it("formats absence separately from genuine zero", () => {
    expect(format(undefined)).toBe("Unavailable");
    expect(format(NaN)).toBe("Unavailable");
    expect(format(0)).toBe("0");
  });
  it("excludes only missing ground observations", () => {
    expect(observed({ ...row, delivered: false }, true)).toBeUndefined();
    expect(observed(row, false)).toBe(row);
  });
  it("breaks paths on absent packets without bridging them", () => {
    const rows = [
      row,
      { ...row, tick: 1, payloads: 2, delivered: false },
      { ...row, tick: 2, payloads: 3 },
    ];
    expect(paths(rows, "payloads", true, 3)).toHaveLength(2);
    expect(paths(rows, "payloads", false, 3)).toHaveLength(1);
    expect(paths(rows, "committed", true, 0)[0]).toContain("170.00");
  });
  it("handles empty and entirely missing series", () => {
    expect(paths([], "payloads", true, 0)).toEqual([]);
    expect(paths([{ ...row, delivered: false }], "payloads", true, 0)).toEqual([]);
  });
});
