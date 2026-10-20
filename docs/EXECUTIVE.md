# Executive model and limits

By Jason Stys. This model teaches software contracts, not spacecraft physics or actual flight operation.

## Tick ordering

The initial frame is tick 0 / BOOT, boot counter 1. Every subsequent integer tick executes:

1. Increment observer clock/sequence; select a finite synthetic port fault.
2. On the checkpoint-corrupt fixture, flip a CRC byte and reset immediately.
3. Complete the two-tick boot delay into STANDBY initially, or latched SAFE after a restart.
4. A servicing non-BOOT executive updates its heartbeat. An independently running supervisor resets a non-BOOT executive when `tick − last_heartbeat >= watchdog`.
5. If the executive can service work, refresh the sensor unless stale, check power index >=300 and sensor age <=5, and latch SAFE on failure.
6. Dispatch the scheduled command after integrity, readiness, ID and health checks.
7. In SCIENCE, increment working payload count on aligned sample ticks.
8. When powered and servicing, write the in-memory checkpoint on aligned checkpoint ticks.
9. Append an end-of-tick observer frame. A missing downlink does not stop onboard work.

There are no threads in the simulated executive, preemptive scheduler, hardware interrupts, wall-clock deadlines or real I/O ports. Independence is explicitly modeled execution order, not measured real-time isolation.

## State and commands

BOOT → STANDBY at tick 2. Valid resume moves STANDBY/SAFE to SCIENCE only when healthy. Valid standby leaves SCIENCE for STANDBY, but cannot clear SAFE. A ping is allowed while unhealthy but never changes mode. A restart returns to BOOT, increments the observer boot counter and requires explicit resume after boot.

Commands: resume ID1 at tick10, duplicate ID1 at20, ping ID2 at fault_tick, resume ID3 at fault_tick+40, standby ID4 at duration−10. A bad CRC/invalid ID/unknown opcode or BOOT receiver is rejected by dispatch without mutation. Duplicates `id <= last_command` are non-mutating. A command arriving when the task is hung or booting is **unserviced**, not a CRC rejection. CRC is not authorization or cryptographic authentication.

Onboard progress consists of last accepted command ID and payload count. Observer counters (accepted/rejected/duplicate/unserviced, lost payloads, boot count, sequence) survive resets to permit analysis. They are not claimed to be onboard nonvolatile hardware counters.

## Checkpoint contract

| Bytes | Meaning                                         |
| ----- | ----------------------------------------------- |
| 0–3   | `FSTB` magic, little-endian uint32 `0x42545346` |
| 4     | Version 1                                       |
| 5–7   | Reserved, must be zero                          |
| 8–11  | Last accepted command ID, LE uint32             |
| 12–15 | Working payload count, LE uint32                |
| 16–19 | CRC32 of bytes0–15, LE uint32                   |

The decoder requires exactly20bytes, expected magic/version/reserved values, CRC and each counter <=1,000,000 before returning progress. No raw struct serialization, padding, ABI or host-endian assumptions. CRC uses reflected polynomial `0xEDB88320`, initial/final XOR `0xFFFFFFFF`; standard `123456789` check is `0xCBF43926`. CRC detects accidental corruption only. A forged CRC is possible and not a supported trust boundary.

Checkpoints live entirely in simulated RAM. They are atomic array assignments in a single-threaded model, **not** validated filesystem durability, redundant NVM, crash consistency or recovery after host power loss. Valid restore loses only uncommitted work. Invalid restore uses zero progress and records the entire previous working count as lost. All supported fixtures contain at most one reset. Replaying a restored command high-water mark is intentionally not a globally persistent anti-replay protocol.

## Independent default expectations

| Scenario           | Key transition                              | End payloads | Lost | Missing frames |
| ------------------ | ------------------------------------------- | ------------ | ---- | -------------- |
| nominal            | SCIENCE10, STANDBY230                       | 110          | 0    | 0              |
| watchdog-hang      | Reset124, SAFE126, resume160                | 87           | 3    | 0              |
| sensor-stale       | SAFE125, sensor fresh136, resume160         | 93           | 0    | 0              |
| telemetry-gap      | Frames120–131 absent, science continues     | 110          | 0    | 12             |
| checkpoint-corrupt | Reject/reset120, SAFE122, resume160         | 35           | 55   | 0              |
| brownout           | SAFE120, power recovers132, resume160       | 90           | 0    | 0              |
| command-corrupt    | Ping120 rejected; high-water mark unchanged | 110          | 0    | 0              |

Watchdog reset is `fault_tick + watchdog − 1`, because the last heartbeat is fault_tick−1. Staleness triggers at fault_tick+5, when age first exceeds5. Nominal payload count is the number of sample-aligned ticks in `[10, duration−10)`. These arithmetic expectations are independently tested, not merely golden screenshots.

## Complexity

For T ticks and E events: simulation O(T+E) time and O(T+E) returned evidence memory; per-tick work is O(1). Checkpoint codec is fixed20bytes (O(1)); CRC is O(B) in the span length, fixed16/8bytes for checkpoints/commands. JSON serialization, validation, hashing, report exports and plot creation are O(T+E); the UI reuses a cursor for O(1) per replay step, though changing perspective redraws O(T). The serialized native cache holds at most32 finite experiment results, returning detached objects. Settings cap T at480; this is a bounded teaching workload, not a throughput benchmark or hard real-time guarantee.

No radiation, fuel, orbital dynamics, targeting, actual flight-controller API, spacecraft coordinates, propulsion, hardware addresses or operational telemetry are present. External scientific/flight applicability has not been established.
