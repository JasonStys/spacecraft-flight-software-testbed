/* Simulated spacecraft executive contracts by Jason Stys.
 * Types: Config, Mode, Opcode, Command, Decision, Sample, Event, Report.
 * Functions: validate, make_command, dispatch, simulate. Variable lines: docs/CODE_INDEX.md.
 * No real hardware, guidance, orbital dynamics, flight qualification or weapon interfaces.
 */
#pragma once
#include "checkpoint.hpp"
#include <string>
#include <vector>

namespace flight {
/** Logical states; SAFE is a teaching software mode, not a real-vehicle safety assertion. */
enum class Mode { boot, standby, science, safe };
enum class Opcode : std::uint8_t { ping, resume, standby };
enum class Decision { accepted, rejected, duplicate };
/** Finite software-in-the-loop experiment; every device and clock is synthetic. */
struct Config {
    std::string scenario = "nominal";
    int duration = 240;
    int fault_tick = 120;
    int watchdog = 5;
    int checkpoint_period = 8;
    int sample_period = 2;
};
/** In-memory command fixture with CRC; no network or device command receiver exists. */
struct Command {
    std::uint32_t id;
    Opcode opcode;
    std::uint32_t checksum;
};
/** End-of-tick observer frame; delivered=false marks an absent downlink, not zero telemetry. */
struct Sample {
    int tick = 0;
    int uptime = 0;
    int boot = 1;
    Mode mode = Mode::boot;
    int sensor_age = 0;
    int sensor_value = 0;
    bool sensor_valid = false;
    int power_score = 900;
    int payloads = 0;
    int committed = 0;
    int lost_payloads = 0;
    int accepted = 0;
    int rejected = 0;
    int duplicates = 0;
    int unserviced = 0;
    int watchdog_age = 0;
    int sequence = 0;
    bool delivered = true;
    bool fault_active = false;
};
/** Fixed vocabulary event with logical time and a bounded integer diagnostic value. */
struct Event { int tick; std::string type; int value; };
struct Report { std::vector<Sample> samples; std::vector<Event> events; };
/** Reject unsupported workloads and fixture choices before starting the executive. */
void validate(const Config& config);
/** Return a fixed display label for a valid enum; invalid enum is rejected. */
std::string mode_name(Mode mode);
/** Make a canonical fixture checksum for command contract tests and scheduled scripts. */
Command make_command(std::uint32_t id, Opcode opcode);
/** Check framing/checksum, monotonic IDs, readiness and health before any state mutation. */
Decision dispatch(const Command& command, Progress& progress, Mode& mode, bool healthy);
/** Execute one deterministic bounded mission with software-only device ports and fault fixtures. */
Report simulate(const Config& config);
} // namespace flight
