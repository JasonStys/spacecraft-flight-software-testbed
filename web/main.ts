/* Local experiment orchestration and replay UI by Jason Stys.
 * Functions: element, text, pause, render, chart, load, configure, start.
 * Variables: catalog, run, generation, controller, tick and single-owner animation frame.
 * Contracts/variable lines: docs/CODE_INDEX.md. Text-only DOM writes; no remote APIs.
 */
import "./style.css";
import { format, observed, paths, preferences } from "./model";
import type { Catalog, Run, Settings } from "./types";

/** Require the authored DOM contract instead of continuing with null elements. */
function element<T extends HTMLElement>(id: string): T {
  const result = document.getElementById(id);
  if (!result) throw new Error(`Missing UI element ${id}`);
  return result as T;
}
/** Render untrusted evidence as text, never active HTML. */
function text(id: string, value: string): void {
  element(id).textContent = value;
}
let catalog: Catalog;
let run: Run | undefined;
let generation = 0;
let controller: AbortController | undefined;
let frame: number | undefined;
let lastTime = 0;
let tick = 0;

/** Cancel the actual pending frame; repeated play/pause cannot accumulate replay loops. */
function pause(): void {
  if (frame !== undefined) cancelAnimationFrame(frame);
  frame = undefined;
  lastTime = 0;
  text("play", "Play replay");
}
/** Build finite settings from authored select controls; the service validates independently. */
function settings(): Settings {
  const data = Object.fromEntries(new FormData(element<HTMLFormElement>("config")));
  return Object.fromEntries(
    Object.entries(data).map(([key, value]) => [
      key,
      key === "scenario" ? String(value) : Number(value),
    ]),
  ) as unknown as Settings;
}
/** Draw all-run reference/experiment counters with explicit gaps and a replay cursor. */
function chart(): void {
  if (!run) return;
  const svg = element("chart");
  svg.replaceChildren();
  const ground = element<HTMLSelectElement>("perspective").value === "ground";
  const maximum = Math.max(1, run.summary.reference_payloads ?? 1);
  for (const [rows, field, color, received] of [
    [run.reference.samples, "payloads", "#93a8c1", false],
    [run.experiment.samples, "committed", "#ffc582", ground],
    [run.experiment.samples, "payloads", "#89e5cc", ground],
  ] as const) {
    for (const path of paths(rows, field, received, maximum)) {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
      line.setAttribute("d", path);
      line.setAttribute("fill", "none");
      line.setAttribute("stroke", color);
      line.setAttribute("stroke-width", "2");
      line.setAttribute("data-series", field);
      svg.append(line);
    }
  }
  const cursor = document.createElementNS("http://www.w3.org/2000/svg", "line");
  cursor.id = "cursor";
  cursor.setAttribute("y1", "0");
  cursor.setAttribute("y2", "180");
  cursor.setAttribute("stroke", "#e2ebe8");
  cursor.setAttribute("stroke-dasharray", "3 4");
  svg.append(cursor);
  render();
}
/** At a missing packet show no current values; never substitute zero or unlabelled carry-forward. */
function render(): void {
  if (!run) return;
  const current = run.experiment.samples[tick];
  if (!current) return;
  const sample = observed(current, element<HTMLSelectElement>("perspective").value === "ground");
  text("tick-label", String(tick));
  element<HTMLInputElement>("tick").value = String(tick);
  text("frame-state", sample ? `FRAME ${sample.sequence} / RECEIVED` : "NO DOWNLINK FRAME");
  text("mode", sample?.mode ?? "Unavailable");
  text(
    "boot",
    sample ? `Boot ${sample.boot} · uptime ${sample.uptime} ticks` : "No current observation",
  );
  text("payloads", sample ? `${sample.payloads} / ${sample.committed}` : "Unavailable");
  text(
    "loss",
    sample ? `${sample.lost_payloads} volatile payloads lost` : "No current observation",
  );
  text("watchdog-age", sample ? `${sample.watchdog_age} ticks` : "Unavailable");
  text("sensor", sample?.sensor_valid ? `${sample.sensor_age} ticks old` : "Unavailable");
  text(
    "power",
    sample ? `Power index ${sample.power_score} · synthetic` : "No current observation",
  );
  for (const state of document.querySelectorAll<HTMLElement>("[data-mode]"))
    state.classList.toggle("active", state.dataset.mode === sample?.mode);
  const x = (tick / run.settings.duration) * 900;
  element("cursor").setAttribute("x1", String(x));
  element("cursor").setAttribute("x2", String(x));
}
/** Render bounded omniscient events, clearly separate from the ground-view frame selection. */
function ledger(): void {
  const list = element("events");
  list.replaceChildren();
  for (const event of run?.experiment.events ?? []) {
    if (event.type === "checkpoint-saved" && !element<HTMLInputElement>("checkpoints").checked)
      continue;
    const item = document.createElement("li");
    const time = document.createElement("time");
    time.textContent = `T+${event.tick}`;
    item.append(time, `${event.type.replaceAll("-", " ")} · ${event.value}`);
    list.append(item);
  }
}
/** Clear stale evidence while running; only the latest request may publish a result. */
async function load(): Promise<void> {
  pause();
  controller?.abort();
  controller = new AbortController();
  const active = ++generation;
  const selected = settings();
  element("results").hidden = true;
  element("retry").hidden = true;
  run = undefined;
  text("status", "Running bounded native executive and nominal reference…");
  element<HTMLButtonElement>("apply").disabled = true;
  try {
    const query = new URLSearchParams(
      Object.entries(selected).map(([key, value]) => [key, String(value)]),
    );
    const response = await fetch(`/api/run?${query}`, { signal: controller.signal });
    if (!response.ok) throw new Error("Local executive unavailable");
    const data = (await response.json()) as Run;
    if (active !== generation) return;
    run = data;
    tick = 0;
    try {
      localStorage.setItem("flight-settings-v1", JSON.stringify(selected));
    } catch {
      /* Storage is optional. */
    }
    element<HTMLInputElement>("tick").max = String(run.settings.duration);
    const summary = element("summary");
    summary.replaceChildren();
    for (const [key, label] of [
      ["resets", "Resets"],
      ["lost_payloads", "Volatile loss"],
      ["missing_frames", "Missing frames"],
      ["safe_ticks", "SAFE ticks"],
      ["rejected", "Rejected commands"],
      ["duplicates", "Duplicate commands"],
    ] as const) {
      const group = document.createElement("dl");
      const title = document.createElement("dt");
      const value = document.createElement("dd");
      title.textContent = label;
      value.textContent = format(run.summary[key]);
      group.append(title, value);
      summary.append(group);
    }
    for (const formatName of ["json", "csv", "html"])
      element<HTMLAnchorElement>(`download-${formatName}`).href =
        `/api/report?${query}&format=${formatName}`;
    text("fingerprint", `Evidence ${run.id}\nTrajectory ${run.provenance.trajectory_sha256}`);
    element("results").hidden = false;
    chart();
    ledger();
    text(
      "status",
      `Complete · ${run.experiment.samples.length} frames · deterministic ${run.scenario} replay`,
    );
  } catch (error) {
    if (active !== generation || (error instanceof DOMException && error.name === "AbortError"))
      return;
    text(
      "status",
      "Experiment failed. No previous result is displayed. Check the local service, then retry.",
    );
    element("retry").hidden = false;
  } finally {
    if (active === generation) element<HTMLButtonElement>("apply").disabled = false;
  }
}
/** Schedule one animation owner; elapsed time drives a bounded ten-ticks-per-second replay. */
function animate(time: number): void {
  if (!run) {
    pause();
    return;
  }
  if (!lastTime) lastTime = time;
  const steps = Math.floor((time - lastTime) / 100);
  if (steps) {
    tick = Math.min(run.settings.duration, tick + steps);
    lastTime += steps * 100;
    render();
  }
  if (tick >= run.settings.duration) {
    pause();
    return;
  }
  frame = requestAnimationFrame(animate);
}
/** Assign finite controls and explain the selected fault; no arbitrary source or device input. */
function configure(value: Settings): void {
  for (const [key, entry] of Object.entries(value))
    element<HTMLSelectElement>(key).value = String(entry);
  text("scenario-description", catalog.scenarios[value.scenario] ?? "");
}
/** Fetch catalog before wiring replay; service errors remain recoverable through reload. */
async function start(): Promise<void> {
  try {
    const response = await fetch("/api/catalog");
    if (!response.ok) throw new Error("Catalog unavailable");
    catalog = (await response.json()) as Catalog;
    for (const [value] of Object.entries(catalog.scenarios))
      element("scenario").append(new Option(value.replaceAll("-", " "), value));
    for (const [key, choices] of Object.entries(catalog.choices))
      for (const value of choices) element(key).append(new Option(String(value), String(value)));
    let raw: string | null = null;
    try {
      raw = localStorage.getItem("flight-settings-v1");
    } catch {
      /* Private/blocked storage is supported. */
    }
    configure(preferences(raw, catalog));
    element("config").addEventListener("submit", (event) => {
      event.preventDefault();
      void load();
    });
    element("scenario").addEventListener("change", () =>
      text(
        "scenario-description",
        catalog.scenarios[element<HTMLSelectElement>("scenario").value] ?? "",
      ),
    );
    element("reset").addEventListener("click", () => {
      configure(catalog.defaults);
      void load();
    });
    element("retry").addEventListener("click", () => void load());
    element("perspective").addEventListener("change", chart);
    element("checkpoints").addEventListener("change", ledger);
    element("tick").addEventListener("input", () => {
      pause();
      tick = Number(element<HTMLInputElement>("tick").value);
      render();
    });
    element("play").addEventListener("click", () => {
      if (frame !== undefined) {
        pause();
        return;
      }
      if (tick >= (run?.settings.duration ?? 0)) tick = 0;
      text("play", "Pause replay");
      frame = requestAnimationFrame(animate);
    });
    window.addEventListener("pagehide", () => {
      pause();
      controller?.abort();
    });
    await load();
  } catch {
    text(
      "status",
      "Cannot load local configuration. Restart the local service and reload this page.",
    );
  }
}
void start();
