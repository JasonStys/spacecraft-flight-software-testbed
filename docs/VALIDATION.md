# Validation and test evidence

By Jason Stys. Local results recorded 2026-10-20. GitHub CI/release evidence is added after actual execution; planned gates are not claimed as completed runs.

## Local results

| Check                                   | Observed result                                                                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| C++20 MSVC Release / warnings as errors | Build passed; CTest3/3 passed                                                                                                          |
| Executive configuration contracts       | 756 scenario/configuration combinations passed                                                                                         |
| Checkpoint/command tests                | Known CRC check vector, endian layout, boundaries, all160 single-bit flips, malformed lengths/version/reserved/counter cases passed    |
| Bounded seeded byte fuzz                | 5,000 deterministic malformed byte spans passed; not coverage-guided fuzzing or proof of parser security                               |
| Python tests                            | 78 passed; branch-aware application coverage99.43%, required90%                                                                        |
| Hypothesis                              | 40 finite random configuration examples plus deterministic scenario/oracle checks                                                      |
| TypeScript pure tests                   | 12 passed                                                                                                                              |
| Browser checks                          | 21/21 passed locally across Chromium/Firefox/WebKit, including real downloads, replay, failures, accessibility and 390px layout        |
| Ruff / strict mypy / TypeScript build   | Passed locally                                                                                                                         |
| Integer replay fixtures                 | Seven default scenarios saved in reports/replay-contracts.json and verified against independent deadline/count assertions              |
| Cold native process timing              | 15 watchdog480 runs: median15.16ms, maximum22.55ms on this Windows/MSVC host, includes spawn/JSON; observational, no latency guarantee |

### Requirements to tests

| Requirement / failure                | Evidence                                                                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Exact reset and latched recovery     | native/tests.cpp; test_engine.py independent tick124/126/160 assertions                                                                    |
| Checkpoint correctness / loss        | native codec byte tests; Python restored52/lost3 and corrupt-checkpoint lost55 assertions                                                  |
| Commands/checksums/idempotence       | Native invalid/Boot/unhealthy/duplicate tests; Python rejection/unserviced counters                                                        |
| Missing telemetry honesty            | Native12-frame invariants; Python exact missing-tick set; browser unavailable metrics and split SVG paths                                  |
| Cross-build determinism              | Fresh process comparison; golden hashes verified on all CI Python/OS jobs                                                                  |
| Bad process output                   | Timeout/nonzero/JSON/schema/size mocks and controlled errors                                                                               |
| Confidentiality/origin/path boundary | Actual loopback HTTP tests for traversal, symlinks, Host/Origin/cross-site, methods, duplicate/excessive/long queries and header injection |
| Portable reports/history             | Actual CLI/CSV/JSON/HTML/SQLite tests, immutable rows, idempotence, hash mismatch and cap refusal                                          |
| Browser usability                    | 3engines,390px layout, axe WCAG2A/AA/2.1AA scan, blocked storage, real downloads, retry and single-owner paused replay with virtual time   |
| Native memory/UB                     | CI Clang AddressSanitizer+UndefinedBehaviorSanitizer runs all native tests                                                                 |
| Native executed line coverage        | CI GCC/gcovr gate>=90% over core/checkpoint/CLI; tests themselves excluded                                                                 |
| Distributable behavior               | Actual frozen app export/web/worker/resource smoke on Windows/Linux/macOS                                                                  |

## CI gates

Validation has10jobs: four Python/OS combinations (Linux3.12/3.14, Windows/macOS3.14), one Chromium/Firefox/WebKit integration job, three native bundle jobs, one ASan+UBSan job and one GCC coverage job. CodeQL has3 language jobs with security-and-quality queries. Python and npm dependency audits execute; workflows are pinned, least-privilege scoped, and no new Actions artifacts/caches are created. Exact run links/results will be recorded after first pass.

## Interpretation and limits

All oracles target this documented **synthetic software contract**, not actual hardware, physical spacecraft behavior, fault tolerance certification, radiation effects, scheduling jitter, hard real time, flight qualification or complete security. Golden fixtures alone could preserve a wrong model; independent arithmetic/deadline tests supplement them. The deterministic seeded byte corpus is not exhaustive, mutation testing or long-running coverage-guided fuzzing. Automated accessibility scans are useful but not a full human accessibility audit. Mobile browser responsiveness is tested; mobile-native packaging is not supplied. Windows packaged execution can be tested on this PC; Linux/macOS native execution is performed on their CI runners, not claimed locally.

Storage preflight: account REST inventory found58,024,434 live artifact bytes and15,203,216,587 separate cache bytes; billing UI showed0.5/0.5GB (100%) included Actions storage. These meters differ because billing is accumulated, not the current live byte inventory. Nothing was deleted. This repo avoids artifact/cache uploads; public job execution remains subject to account policy/service availability.
