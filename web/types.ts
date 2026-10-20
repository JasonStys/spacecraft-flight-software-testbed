/* Browser evidence contracts by Jason Stys. Types: Settings, Sample, Event, Run.
 * Variables/fields and exact lines: docs/CODE_INDEX.md. Counters are synthetic, not vehicle telemetry.
 */
export interface Settings {
  scenario: string;
  duration: number;
  fault_tick: number;
  watchdog: number;
  checkpoint_period: number;
  sample_period: number;
}
export interface Sample {
  tick: number;
  uptime: number;
  boot: number;
  mode: string;
  sensor_age: number;
  sensor_value: number;
  sensor_valid: boolean;
  power_score: number;
  payloads: number;
  committed: number;
  lost_payloads: number;
  accepted: number;
  rejected: number;
  duplicates: number;
  unserviced: number;
  watchdog_age: number;
  sequence: number;
  delivered: boolean;
  fault_active: boolean;
}
export interface FlightEvent {
  tick: number;
  type: string;
  value: number;
}
export interface Series {
  samples: Sample[];
  events: FlightEvent[];
}
export interface Run {
  id: string;
  scenario: string;
  settings: Settings;
  experiment: Series;
  reference: Series;
  summary: Record<string, number>;
  provenance: { trajectory_sha256: string; worker_sha256: string; clock: string };
}
export interface Catalog {
  scenarios: Record<string, string>;
  choices: Record<string, number[]>;
  defaults: Settings;
}
