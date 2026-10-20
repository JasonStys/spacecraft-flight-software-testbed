# Architecture and decisions

By Jason Stys. Status: accepted for a local educational portfolio application.

```text
Finite browser controls → loopback Python API → fixed C++ worker
       ↑                         ↓                   ↓
TypeScript replay ← strict JSON validation ← deterministic integer frames
                                  ↓
                     JSON / CSV / inert HTML
CLI only → optional immutable SQLite history
```

## ADR1 — Original small executive, not a flight framework integration

NASA describes reusable architectures such as cFS and software-only development tools such as NOS3. Its catalog distinguishes lab applications from a flight distribution. This project applies the software-in-the-loop teaching idea through an original minimal executive, with no claim of cFS API compatibility, NOS3 integration or agency endorsement. [NASA mission design tools](https://www.nasa.gov/smallsat-institute/space-mission-design-tools/), [The State of NOS3](https://ntrs.nasa.gov/citations/20240004699).

Why: a small deterministic contract is inspectable in interviews and practical for sanitizer/fault tests. Trade-off: it lacks a real software bus, RTOS, device drivers, scheduler analysis and actual flight applications. Real mission use requires a completely different engineering and assurance program.

## ADR2 — Use each language at a narrow boundary

C++20 models explicit state, canonical bytes, command checks and per-tick behavior under compiler warnings and sanitizers. TypeScript provides strict view contracts, portable DOM/SVG and a lightweight offline interface without a framework runtime. Python's standard library owns bounded process orchestration, evidence hashing, reports, local HTTP and packaging. SQL provides transactional, parameterized, opt-in history. HTML/CSS provide semantic responsive presentation. Extra languages would not improve this project; no arbitrary compiler/model/plugin loading exists.

The worker accepts exactly six fixed arguments, no shell. Output is validated before display or export. Crash/timeout/nonzero/invalid schema fail closed, never fall back to fabricated success. Build SHA and deterministic trajectory hashes distinguish source/build provenance from experiment behavior.

## ADR3 — Finite integer experiments

Integer ticks/counters avoid floating-point platform drift and make cross-build byte-for-byte replay contracts possible. Only reviewed scenarios and parameter values are allowed. Alternatives rejected: arbitrary uploaded scripts, real telemetry streams and hardware links, which widen trust/safety scope. Consequence: this is intentionally not a general spacecraft simulator.

## ADR4 — Local read-only web interface and portable bundles

Only IPv4 loopback is bound. HTTP provides no file upload, account, mutation, history or external fetch endpoints. Native bundle launches a local browser service; no public domain, cloud bill, admin installation, persistent background service or phone-native binary. Remote/public hosting would require a separate security design and user approval.

## ADR5 — Evidence over hidden results

The entire run and nominal reference are downloadable. Full-run summary/ledger/reference are explicitly simulator-observer truth; received-only views suppress absent frames and break chart segments. Do not infer zeros or interpolate hidden telemetry. History uses content hashes, immutable triggers and a100-run cap, not a security claim against a privileged filesystem user. Defaults are reproducible; timings are measured observations, not absolute performance promises.

## ADR6 — Storage-conscious delivery

The account billing meter is currently full. CI uses no Actions artifact upload or cache actions (including disabled automatic Node/CodeQL caches). Job logs remain on GitHub. Portable release files upload directly to a draft release, with exact-source passing-workflow gates. No existing account runs/caches are deleted by this repo. Release assets are distinct from Actions storage.

Extension points are compile-time scenario/core changes plus validated schema tests. Add new states/ports only with independent contracts, versioned evidence changes, updated threat model and refreshed reviewed replay fixtures. Do not connect real flight systems.
