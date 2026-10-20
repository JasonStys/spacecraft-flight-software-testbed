# User guide

By Jason Stys. Use only the supplied synthetic fixtures.

## Five-minute experiment

1. Start the portable app, or build from source and run `python -m flightlab serve`. A loopback URL opens in your browser; no Internet connection is needed for running experiments.
2. Select `watchdog hang`, leave the finite defaults, and choose **Run experiment**.
3. Scrub to tick 123: science is hung but the watchdog deadline has not yet expired. At 124 the independent supervisor resets the executive. Tick 126 completes boot into SAFE. The scheduled healthy resume at 160 returns to SCIENCE.
4. Compare working vs committed counters: three uncommitted payloads were lost. The 52 committed payloads restore from the tick-112 checkpoint. End-of-run working/committed counters are 87 rather than the nominal 110.
5. Try `telemetry gap`, select **Received downlink only**, and scrub to 125. Current measurements are unavailable and curves break over ticks 120–131. Switch to onboard truth to inspect the simulation's hidden state. The reference curve and full-run ledger/summary are explicitly omniscient.
6. Download JSON, CSV or inert HTML. Full evidence includes the settings, both series, events, summaries and provenance. No personal data is included.

## Controls

| Setting        | Allowed values          | Meaning                                                            |
| -------------- | ----------------------- | ------------------------------------------------------------------ |
| Scenario       | Seven reviewed fixtures | One deterministic fault per experiment; no arbitrary event scripts |
| Duration       | 240 / 480               | Number of logical ticks; includes tick-zero frame                  |
| Inject at      | 80 / 120 / 160          | Start of the selected finite fault                                 |
| Watchdog       | 3 / 5 / 8               | Missing-heartbeat deadline, measured from last successful tick     |
| Checkpoint     | 4 / 8 / 16              | Save period, conditional on powered, servicing executive           |
| Science sample | 2 / 4                   | Produce one synthetic payload on aligned SCIENCE ticks             |

Settings remain pending until Run experiment; downloaded evidence always uses the last completed run's settings. Defaults resets and runs. Browser storage keeps only finite settings; storage denial or malformed preferences does not prevent operation. Replay has one animation owner, stops at the final frame, and pauses when scrubbed or a new run starts.

## Fault interpretation

The watchdog's hang is consumed by the first reset. Sensor staleness lasts 16 ticks; low synthetic power lasts 12; telemetry absence lasts 12. Corrupt checkpoint and corrupt command are one-tick injections. SAFE remains latched even after the port recovers; it is cleared only by a new valid resume while healthy. A reset's triggering tick cannot service the scheduled ping; this is counted separately from an explicit rejection. Commands are fixed fixtures, not user-issued hardware commands.

Unavailable sensor values during boot are not measured zeros. Sensor age can increase while an executive is hung. Downlink sequence is a simulator-observer sequence and survives resets; it is not a wire protocol implementation. No physical sensor value is modeled.

## Reports and local history

JSON preserves complete structured evidence. CSV contains both experiment and reference rows, delivery flags, sensor validity and integer counters. HTML is escaped, has no scripts, and can be opened offline. CSV text labels are fixed, not uploaded spreadsheet formulas.

Use `python -m flightlab export --help` for the CLI. `--history path.sqlite3` explicitly opts into local SQLite history. Same evidence is idempotent, tampered evidence is refused, and existing rows cannot be updated or deleted through the schema. The 100-run cap refuses a new run without deleting anything; choose a new database to continue. Local OS users with file access can still change files—immutability is an application contract, not an access-control system.

## Troubleshooting

- **Native worker missing:** rebuild with `python tools/build_native.py`; do not download an arbitrary executable into the worker directory.
- **Website build missing:** run `npm ci` and `npm run build`.
- **No result:** retry after checking the local console. Old evidence is hidden on failure; it is never relabeled as a new success.
- **Port busy:** use the default ephemeral port or choose a free `--port`. Only IPv4 loopback is accepted; use `127.0.0.1`, not `localhost` or an external hostname.
- **Download already exists:** the CLI never overwrites it. Choose a new filename. History/export are separate destinations, not a cross-file transaction.
- **App blocked by the OS:** builds are unsigned. Do not bypass warnings or disable protections; build from reviewed source or wait for a trusted signed distribution.

Contact [Jason Stys](https://github.com/JasonStys) or open an issue. Include synthetic settings/replay hash, not sensitive files. No public hosting, mobile-native installer, operating-system service or background telemetry is installed.
