# Local API and evidence schema

By Jason Stys. Read-only, same-origin HTTP, exact Host `127.0.0.1:<port>`. No CORS, user accounts or uploads.

| GET route                    | Response                                                |
| ---------------------------- | ------------------------------------------------------- |
| `/api/health`                | Status and local educational mode; no worker invocation |
| `/api/catalog`               | Scenario descriptions, finite choices and defaults      |
| `/api/run`                   | Complete schema1 JSON with selected defaults/settings   |
| `/api/report?format=json`    | JSON attachment; also `csv`, `html`                     |
| `/` / `/assets/<built-name>` | Reviewed built HTML/JS/CSS/SVG/ICO only                 |

Run/report queries accept `scenario`, `duration`, `fault_tick`, `watchdog`, `checkpoint_period`, `sample_period`, and report-only `format`. Settings are listed in USER_GUIDE. Duplicates, unknown keys, blank/unsupported values, excessive fields and noninteger choices are refused. Query conversion accepts Python integer textual spelling (e.g. `0240`) but canonical evidence always contains the same numeric240. Requests longer than1024characters are rejected. Status400 invalid input,403 origin/Host/cross-site refusal,404 missing/unsafe assets,405 write methods/HEAD,414 long URL,500 unavailable worker/local resource. Errors never echo source paths or raw input. No arbitrary filesystem routes.

## JSON schema1

`id`: SHA256 of sorted compact UTF-8 JSON of all fields except id. `scenario`/`settings`: full finite input. `experiment`/`reference`: each has `samples` and `events`. `summary`: observer-derived counts. `provenance`: author/version, logical clock, worker-byte SHA256, platform-independent experiment replay SHA256, scope and invented units.

Samples have: tick, uptime, boot, mode, sensor_age, sensor_value, sensor_valid, power_score, payloads, committed, lost_payloads, accepted, rejected, duplicates, unserviced, watchdog_age, sequence, delivered, fault_active. Numeric fields are bounded nonnegative integers, mode is a fixed enum label, flags are booleans. There are duration+1frames. Unavailable sensor value0 is a sentinel only when sensor_valid=false. False delivered means **no ground observation**; full evidence still retains simulator truth for inspection. Sequence is observer tick, not a CCSDS packet count.

Events are ordered fixed-vocabulary `{tick,type,value}` records: initial-boot, fault-injected, checkpoint-restored/rejected/saved, integrity-reset, watchdog-reset, boot-complete-safe/standby, power-low, sensor-stale, command-accepted/rejected/duplicate/unserviced. Event value is an integer counter/command ID, not free-form uploaded text. Full event/field vocabulary is validated at the Python process boundary.

The worker is invoked as `flight_core <scenario> <duration> <fault_tick> <watchdog> <checkpoint_period> <sample_period>`. Full-token integer parsing rejects fractional, trailing and overflow input. Timeout5seconds; a bounded reviewed workload produces at most481frames. The2MB stdout check happens after capture; it is a sanity check on a trusted bundled executable, not an OS memory sandbox for arbitrary programs. No arbitrary executable selection is exposed.

CSV includes run hash, series, logical clock and all sample fields for both experiment/reference, including delivery and validity. HTML is escaped JSON inside an inert document with `default-src 'none'`. Attachment filenames are fixed, not derived from caller strings.
