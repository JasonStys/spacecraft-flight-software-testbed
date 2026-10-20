/* Release-active native contracts and bounded byte fuzzing by Jason Stys.
 * Functions: require, rejects, checkpoint_tests, command_tests, executive_tests, main.
 * Variables: seeded byte corpus, fixture grid, independent expected deadlines.
 * Exact declaration/variable inventory: docs/CODE_INDEX.md. No assert/NDEBUG dependence.
 */
#include "core.hpp"
#include <array>
#include <iostream>
#include <stdexcept>

namespace {
/** Keep every contract enabled in optimized Release and sanitizer builds. */
void require(bool condition) { if (!condition) throw std::runtime_error("Native contract failed"); }
/** Verify that a public invalid configuration fails closed. */
void rejects(const flight::Config& config) {
    bool rejected = false;
    try { flight::validate(config); } catch (const std::invalid_argument&) { rejected = true; }
    require(rejected);
}
/** Independent CRC vector, exact endian layout, malformed frames and deterministic byte fuzz. */
void checkpoint_tests() {
    const std::array<std::uint8_t, 9> vector{'1','2','3','4','5','6','7','8','9'};
    require(flight::crc32(vector) == 0xcbf43926U);
    require(flight::crc32({}) == 0U);
    const auto frame = flight::encode_checkpoint({0x10203, 0x40506});
    require(frame[0] == 'F' && frame[1] == 'S' && frame[2] == 'T' && frame[3] == 'B');
    require(frame[8] == 3 && frame[9] == 2 && frame[10] == 1 && frame[11] == 0);
    require(flight::decode_checkpoint(frame) == flight::Progress{0x10203, 0x40506});
    for (std::size_t length = 0; length < frame.size(); ++length)
        require(!flight::decode_checkpoint(std::span(frame).first(length)));
    for (std::size_t index = 0; index < frame.size(); ++index) {
        for (int bit = 0; bit < 8; ++bit) {
            auto changed = frame;
            changed[index] ^= static_cast<std::uint8_t>(1U << bit);
            require(!flight::decode_checkpoint(changed));
        }
    }
    std::array<std::uint8_t, 21> oversized{};
    require(!flight::decode_checkpoint(oversized));
    // Recompute CRC to ensure structural/bounds checks are independent of the checksum.
    for (const std::size_t index : {0U, 4U, 5U, 6U, 7U, 11U, 15U}) {
        auto changed = frame;
        changed[index] = 255;
        const auto crc = flight::crc32(std::span(changed).first(16));
        for (std::size_t byte = 0; byte < 4; ++byte)
            changed[16 + byte] = static_cast<std::uint8_t>(crc >> (8 * byte));
        require(!flight::decode_checkpoint(changed));
    }
    for (const auto progress : {flight::Progress{1000001, 0}, flight::Progress{0, 1000001}}) {
        bool failed = false;
        try { (void)flight::encode_checkpoint(progress); }
        catch (const std::invalid_argument&) { failed = true; }
        require(failed);
    }
    require(flight::decode_checkpoint(flight::encode_checkpoint({1000000, 1000000})).has_value());
    std::uint32_t random = 0x5eed1234U;
    for (int iteration = 0; iteration < 5000; ++iteration) {
        std::array<std::uint8_t, 32> bytes{};
        for (auto& byte : bytes) { random = random * 1664525U + 1013904223U; byte = static_cast<std::uint8_t>(random >> 24); }
        const auto parsed = flight::decode_checkpoint(std::span(bytes).first(static_cast<std::size_t>(iteration % 33)));
        require(!parsed);
    }
}
/** Command integrity/readiness/idempotence contracts must not mutate rejected state. */
void command_tests() {
    using namespace flight;
    Progress progress;
    Mode mode = Mode::boot;
    require(dispatch(make_command(1, Opcode::resume), progress, mode, true) == Decision::rejected);
    mode = Mode::standby;
    require(dispatch(make_command(0, Opcode::ping), progress, mode, true) == Decision::rejected);
    require(dispatch(make_command(1000001, Opcode::ping), progress, mode, true) == Decision::rejected);
    require(dispatch(make_command(1, static_cast<Opcode>(255)), progress, mode, true) == Decision::rejected);
    auto broken = make_command(1, Opcode::resume); broken.checksum ^= 1;
    require(dispatch(broken, progress, mode, true) == Decision::rejected);
    require(dispatch(make_command(1, Opcode::resume), progress, mode, false) == Decision::rejected);
    require(progress.last_command == 0 && mode == Mode::standby);
    require(dispatch(make_command(1, Opcode::resume), progress, mode, true) == Decision::accepted);
    require(mode == Mode::science && progress.last_command == 1);
    require(dispatch(make_command(1, Opcode::standby), progress, mode, true) == Decision::duplicate);
    require(mode == Mode::science);
    mode = Mode::safe;
    require(dispatch(make_command(2, Opcode::standby), progress, mode, true) == Decision::rejected);
    require(dispatch(make_command(2, Opcode::ping), progress, mode, false) == Decision::accepted);
    require(dispatch(make_command(3, Opcode::resume), progress, mode, true) == Decision::accepted);
    require(dispatch(make_command(4, Opcode::standby), progress, mode, true) == Decision::accepted);
    require(mode_name(mode) == "STANDBY" && mode_name(Mode::boot) == "BOOT");
    require(mode_name(Mode::science) == "SCIENCE" && mode_name(Mode::safe) == "SAFE");
    bool failed = false;
    try { (void)mode_name(static_cast<Mode>(99)); } catch (const std::invalid_argument&) { failed = true; }
    require(failed);
}
/** Cross-product invariants plus independent expected event deadlines and payload arithmetic. */
void executive_tests() {
    using namespace flight;
    for (const auto& scenario : {"nominal", "watchdog-hang", "sensor-stale", "telemetry-gap", "checkpoint-corrupt", "brownout", "command-corrupt"}) {
        for (const int duration : {240, 480}) for (const int fault : {80,120,160})
        for (const int watchdog : {3,5,8}) for (const int period : {4,8,16})
        for (const int sampling : {2,4}) {
            const Config config{scenario, duration, fault, watchdog, period, sampling};
            const auto report = simulate(config);
            require(report.samples.size() == static_cast<std::size_t>(duration + 1));
            const auto& rows = report.samples;
            require(rows[0].mode == Mode::boot && rows[2].mode == Mode::standby && rows[10].mode == Mode::science);
            require(rows.back().mode == Mode::standby && rows.back().duplicates == 1);
            int missing = 0;
            for (int tick = 0; tick <= duration; ++tick) {
                const auto& row = rows[static_cast<std::size_t>(tick)];
                require(row.tick == tick && row.sequence == tick && row.committed <= row.payloads);
                require(row.sensor_age >= 0 && row.watchdog_age <= watchdog);
                if (!row.delivered) ++missing;
            }
            const std::string name = scenario;
            require(missing == (name == "telemetry-gap" ? 12 : 0));
            if (name == "nominal" || name == "telemetry-gap" || name == "command-corrupt") {
                int expected = 0;
                for (int tick = 10; tick < duration - 10; ++tick) if (tick % sampling == 0) ++expected;
                require(rows.back().payloads == expected && rows.back().boot == 1);
            }
            if (name == "watchdog-hang") {
                const int reset = fault + watchdog - 1;
                require(rows[static_cast<std::size_t>(reset - 1)].boot == 1);
                require(rows[static_cast<std::size_t>(reset)].boot == 2);
                require(rows[static_cast<std::size_t>(reset + 2)].mode == Mode::safe);
                require(rows.back().unserviced == 1);
            }
            if (name == "checkpoint-corrupt") {
                require(rows[static_cast<std::size_t>(fault)].boot == 2);
                require(rows[static_cast<std::size_t>(fault)].payloads == 0);
                require(rows[static_cast<std::size_t>(fault)].lost_payloads > 0);
            }
            if (name == "sensor-stale") {
                require(rows[static_cast<std::size_t>(fault + 4)].mode == Mode::science);
                require(rows[static_cast<std::size_t>(fault + 5)].mode == Mode::safe);
            }
            if (name == "brownout") require(rows[static_cast<std::size_t>(fault)].mode == Mode::safe);
            require(rows[static_cast<std::size_t>(fault + 40)].mode == Mode::science);
            require(rows.back().rejected == (name == "command-corrupt" ? 1 : 0));
        }
    }
    Config invalid;
    invalid.scenario = "unknown"; rejects(invalid); invalid = {};
    invalid.duration = 0; rejects(invalid); invalid = {};
    invalid.fault_tick = -1; rejects(invalid); invalid = {};
    invalid.watchdog = 99; rejects(invalid); invalid = {};
    invalid.checkpoint_period = 0; rejects(invalid); invalid = {};
    invalid.sample_period = 0; rejects(invalid);
}
} // namespace
/** Run independent contracts; exceptions produce a deterministic nonzero test result. */
int main() {
    try { checkpoint_tests(); command_tests(); executive_tests(); std::cout << "756 mission fixtures, codec/command contracts and 5000 byte fuzz cases passed\n"; }
    catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
    return 0;
}
