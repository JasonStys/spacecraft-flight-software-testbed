/* Deterministic executive, supervisor and simulated ports by Jason Stys.
 * Class: Executive. Functions: validate, mode_name, make_command, dispatch, simulate.
 * Variables: logical clock, heartbeat, checkpoint, progress and observer counters.
 * Contracts and exact line inventory: docs/CODE_INDEX.md. Not an RTOS or flight distribution.
 */
#include "core.hpp"
#include <algorithm>
#include <array>
#include <optional>
#include <stdexcept>

namespace flight {
/** Bound both native and public execution; scientific units and hardware addresses are absent. */
void validate(const Config& config) {
    const std::array<std::string, 7> scenarios{"nominal", "watchdog-hang", "sensor-stale",
        "telemetry-gap", "checkpoint-corrupt", "brownout", "command-corrupt"};
    if (std::find(scenarios.begin(), scenarios.end(), config.scenario) == scenarios.end() ||
        (config.duration != 240 && config.duration != 480) ||
        (config.fault_tick != 80 && config.fault_tick != 120 && config.fault_tick != 160) ||
        (config.watchdog != 3 && config.watchdog != 5 && config.watchdog != 8) ||
        (config.checkpoint_period != 4 && config.checkpoint_period != 8 && config.checkpoint_period != 16) ||
        (config.sample_period != 2 && config.sample_period != 4))
        throw std::invalid_argument("Unsupported software-only experiment");
}

/** Convert only known internal states; callers cannot smuggle labels into generated JSON. */
std::string mode_name(Mode mode) {
    switch (mode) {
        case Mode::boot: return "BOOT";
        case Mode::standby: return "STANDBY";
        case Mode::science: return "SCIENCE";
        case Mode::safe: return "SAFE";
    }
    throw std::invalid_argument("Unknown mode");
}

/** Command fixture CRC uses eight explicit bytes: ID and opcode in little endian. */
Command make_command(std::uint32_t id, Opcode opcode) {
    std::array<std::uint8_t, 8> bytes{};
    for (std::size_t i = 0; i < 4; ++i)
        bytes[i] = static_cast<std::uint8_t>((id >> (8 * i)) & 0xffU);
    bytes[4] = static_cast<std::uint8_t>(opcode);
    return {id, opcode, crc32(bytes)};
}

/** Invalid or duplicate commands never advance the persistent command high-water mark. */
Decision dispatch(const Command& command, Progress& progress, Mode& mode, bool healthy) {
    if (command.id == 0 || command.id > progress_limit ||
        static_cast<unsigned>(command.opcode) > static_cast<unsigned>(Opcode::standby) ||
        command.checksum != make_command(command.id, command.opcode).checksum || mode == Mode::boot)
        return Decision::rejected;
    if (command.id <= progress.last_command) return Decision::duplicate;
    if (command.opcode != Opcode::ping && !healthy) return Decision::rejected;
    if (command.opcode == Opcode::standby && mode == Mode::safe) return Decision::rejected;
    if (command.opcode == Opcode::resume) mode = Mode::science;
    if (command.opcode == Opcode::standby) mode = Mode::standby;
    progress.last_command = command.id;
    return Decision::accepted;
}

namespace {
/** Simulated port values selected by a trusted finite scenario, never by hardware/network input. */
struct Inputs {
    bool hung = false;
    bool stale = false;
    bool delivered = true;
    bool corrupt_checkpoint = false;
    bool active = false;
    int power_score = 900;
};

/** A logical-tick executive; supervisor observations survive restart, progress uses checkpoints. */
class Executive {
    Config config_;
    Progress progress_;
    Checkpoint checkpoint_ = encode_checkpoint({});
    Sample state_;
    int heartbeat_ = 0;
    int last_sensor_ = 0;
    int boot_tick_ = 0;
    int ready_tick_ = 2;
    bool restart_safe_ = false;
    Report report_;

    /** Append one bounded diagnostic to the report; no per-event I/O or nondeterministic time. */
    void event(const std::string& type, int value = 0) {
        report_.events.push_back({state_.tick, type, value});
    }

    /** Restore only validated bytes, record volatile loss, and require explicit healthy resume. */
    void restart(const std::string& reason) {
        const auto restored = decode_checkpoint(checkpoint_);
        const auto previous = progress_.payloads;
        progress_ = restored.value_or(Progress{});
        state_.lost_payloads += static_cast<int>(previous - progress_.payloads);
        state_.committed = static_cast<int>(progress_.payloads);
        event(restored ? "checkpoint-restored" : "checkpoint-rejected", state_.committed);
        ++state_.boot;
        state_.mode = Mode::boot;
        state_.sensor_valid = false;
        state_.sensor_value = 0;
        boot_tick_ = state_.tick;
        heartbeat_ = state_.tick;
        last_sensor_ = state_.tick;
        ready_tick_ = state_.tick + 2;
        restart_safe_ = true;
        event(reason, state_.boot);
    }

    /** Scheduled command fixtures: start, deliberate duplicate, ping, healthy resume, standby. */
    std::optional<Command> scheduled() const {
        if (state_.tick == 10 || state_.tick == 20) return make_command(1, Opcode::resume);
        if (state_.tick == config_.fault_tick) {
            auto command = make_command(2, Opcode::ping);
            if (config_.scenario == "command-corrupt") command.checksum ^= 1U;
            return command;
        }
        if (state_.tick == config_.fault_tick + 40) return make_command(3, Opcode::resume);
        if (state_.tick == config_.duration - 10) return make_command(4, Opcode::standby);
        return std::nullopt;
    }

    /** Model a temporary fixture fault; watchdog reset consumes the hanging-task injection. */
    Inputs inputs() const {
        const int elapsed = state_.tick - config_.fault_tick;
        const bool window = elapsed >= 0 && elapsed < 12;
        Inputs input;
        input.hung = config_.scenario == "watchdog-hang" && window && state_.boot == 1;
        input.stale = config_.scenario == "sensor-stale" && elapsed >= 0 && elapsed < 16;
        input.delivered = !(config_.scenario == "telemetry-gap" && window);
        input.corrupt_checkpoint = config_.scenario == "checkpoint-corrupt" && elapsed == 0;
        input.power_score = config_.scenario == "brownout" && window ? 200 : 900;
        input.active = input.hung || input.stale || !input.delivered || input.corrupt_checkpoint ||
            input.power_score < 300 || (config_.scenario == "command-corrupt" && elapsed == 0);
        return input;
    }

    /** Execute supervisor, housekeeping, commands, science and checkpoint in documented order. */
    void advance() {
        ++state_.tick;
        const auto input = inputs();
        state_.sequence = state_.tick; // Observer sequence is independent of onboard restarts.
        state_.delivered = input.delivered;
        state_.fault_active = input.active;
        state_.power_score = input.power_score;
        if (state_.tick == config_.fault_tick && config_.scenario != "nominal") event("fault-injected");
        if (input.corrupt_checkpoint) {
            checkpoint_[16] ^= 1U;
            restart("integrity-reset");
        }
        if (state_.mode == Mode::boot && state_.tick >= ready_tick_) {
            state_.mode = restart_safe_ ? Mode::safe : Mode::standby;
            event(restart_safe_ ? "boot-complete-safe" : "boot-complete-standby");
        }
        if (state_.mode != Mode::boot && !input.hung) heartbeat_ = state_.tick;
        if (state_.mode != Mode::boot && state_.tick - heartbeat_ >= config_.watchdog)
            restart("watchdog-reset");
        const auto command = scheduled();
        if (state_.mode != Mode::boot && !input.hung) {
            if (!input.stale) {
                last_sensor_ = state_.tick;
                state_.sensor_valid = true;
                state_.sensor_value = 490 + state_.tick % 21;
            }
            const bool healthy = input.power_score >= 300 && state_.sensor_valid &&
                state_.tick - last_sensor_ <= 5;
            if (!healthy && state_.mode != Mode::safe) {
                state_.mode = Mode::safe;
                event(input.power_score < 300 ? "power-low" : "sensor-stale");
            }
            if (command) {
                const auto decision = dispatch(*command, progress_, state_.mode, healthy);
                if (decision == Decision::accepted) { ++state_.accepted; event("command-accepted", static_cast<int>(command->id)); }
                if (decision == Decision::rejected) { ++state_.rejected; event("command-rejected", static_cast<int>(command->id)); }
                if (decision == Decision::duplicate) { ++state_.duplicates; event("command-duplicate", static_cast<int>(command->id)); }
            }
            if (state_.mode == Mode::science && state_.tick % config_.sample_period == 0) ++progress_.payloads;
            if (input.power_score >= 300 && state_.tick % config_.checkpoint_period == 0) {
                checkpoint_ = encode_checkpoint(progress_);
                state_.committed = static_cast<int>(progress_.payloads);
                event("checkpoint-saved", state_.committed);
            }
        } else if (command) { ++state_.unserviced; event("command-unserviced", static_cast<int>(command->id)); }
        state_.payloads = static_cast<int>(progress_.payloads);
        state_.uptime = state_.tick - boot_tick_;
        state_.sensor_age = state_.tick - last_sensor_;
        state_.watchdog_age = state_.tick - heartbeat_;
        report_.samples.push_back(state_);
    }

public:
    /** Construct a bounded mission with an initial valid empty checkpoint and boot observer frame. */
    explicit Executive(const Config& config) : config_(config) {
        validate(config_);
        report_.samples.reserve(static_cast<std::size_t>(config.duration) + 1);
        report_.events.reserve(static_cast<std::size_t>(config.duration / config.checkpoint_period) + 24);
        report_.samples.push_back(state_);
        event("initial-boot", 1);
    }
    /** Run exactly duration logical ticks; return owned evidence with no shared mutable state. */
    Report run() {
        for (int tick = 0; tick < config_.duration; ++tick) advance();
        return std::move(report_);
    }
};
} // namespace

/** Keep the public simulation boundary narrow: finite fixtures in, deterministic evidence out. */
Report simulate(const Config& config) { return Executive(config).run(); }
} // namespace flight
