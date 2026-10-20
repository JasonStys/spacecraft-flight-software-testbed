/* Pure display transforms and finite preferences by Jason Stys.
 * Functions: paths, preferences, format, observed. Variables: points/segments/allowed choices.
 * Exact declaration inventory: docs/CODE_INDEX.md. Missing downlink frames break SVG paths.
 */
import type { Catalog, Sample, Settings } from "./types";

/** Render one finite counter; unavailable is never represented as a measured zero. */
export function format(value: number | undefined): string {
  return value === undefined || !Number.isFinite(value)
    ? "Unavailable"
    : value.toLocaleString("en-US");
}
/** Ground perspective excludes absent packets; onboard truth is explicitly a simulator oracle. */
export function observed(sample: Sample, ground: boolean): Sample | undefined {
  return ground && !sample.delivered ? undefined : sample;
}
/** Build separate SVG segments over contiguous received samples, preserving genuine gaps. */
export function paths(
  rows: Sample[],
  field: "payloads" | "committed",
  ground: boolean,
  maximum: number,
): string[] {
  const segments: string[] = [];
  let points: string[] = [];
  const duration = rows.at(-1)?.tick ?? 1;
  for (const row of rows) {
    if (!observed(row, ground)) {
      if (points.length) segments.push(points.join(" "));
      points = [];
    } else {
      points.push(
        `${points.length ? "L" : "M"}${((row.tick / duration) * 900).toFixed(2)},${(170 - (row[field] / Math.max(1, maximum)) * 150).toFixed(2)}`,
      );
    }
  }
  if (points.length) segments.push(points.join(" "));
  return segments;
}
/** Restore only own known primitive choices; poisoned/inherited keys never overwrite defaults. */
export function preferences(raw: string | null, catalog: Catalog): Settings {
  const result = { ...catalog.defaults };
  if (!raw) return result;
  try {
    const data: unknown = JSON.parse(raw);
    if (!data || typeof data !== "object" || Array.isArray(data)) return result;
    for (const [key, value] of Object.entries(data)) {
      if (
        key === "scenario" &&
        typeof value === "string" &&
        Object.hasOwn(catalog.scenarios, value)
      )
        result.scenario = value;
      else if (
        Object.hasOwn(catalog.choices, key) &&
        typeof value === "number" &&
        catalog.choices[key]?.includes(value)
      ) {
        Object.assign(result, { [key]: value });
      }
    }
  } catch {
    /* Malformed local preferences are ignored, never executed. */
  }
  return result;
}
