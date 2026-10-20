/* Fixed JSON executive worker by Jason Stys. Functions: integer, emit, main.
 * Variables: bounded CLI Config, samples and events; locations: docs/CODE_INDEX.md.
 * No networking, shell, hardware I/O, dynamic code or arbitrary input-file loader.
 */
#include "core.hpp"
#include <charconv>
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {
/** Parse an entire integer token; no partial, fractional or overflowing values are accepted. */
int integer(std::string_view token) {
    int value = 0;
    const auto result = std::from_chars(token.data(), token.data() + token.size(), value);
    if (result.ec != std::errc{} || result.ptr != token.data() + token.size())
        throw std::invalid_argument("Invalid integer");
    return value;
}
/** Emit only fixed keys, validated enum labels, fixed event vocabulary, integers and booleans. */
void emit(const flight::Report& report) {
    std::cout << std::boolalpha << "{\"samples\":[";
    bool first = true;
    for (const auto& s : report.samples) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"tick\":" << s.tick << ",\"uptime\":" << s.uptime << ",\"boot\":" << s.boot
            << ",\"mode\":\"" << flight::mode_name(s.mode) << "\",\"sensor_age\":" << s.sensor_age
            << ",\"sensor_value\":" << s.sensor_value << ",\"sensor_valid\":" << s.sensor_valid
            << ",\"power_score\":" << s.power_score << ",\"payloads\":" << s.payloads
            << ",\"committed\":" << s.committed << ",\"lost_payloads\":" << s.lost_payloads
            << ",\"accepted\":" << s.accepted << ",\"rejected\":" << s.rejected
            << ",\"duplicates\":" << s.duplicates << ",\"unserviced\":" << s.unserviced
            << ",\"watchdog_age\":" << s.watchdog_age << ",\"sequence\":" << s.sequence
            << ",\"delivered\":" << s.delivered << ",\"fault_active\":" << s.fault_active << '}';
    }
    std::cout << "],\"events\":[";
    first = true;
    for (const auto& e : report.events) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"tick\":" << e.tick << ",\"type\":\"" << e.type << "\",\"value\":" << e.value << '}';
    }
    std::cout << "]}\n";
}
} // namespace

/** Run six fixed model arguments; invalid input returns 2 and a non-reflective error. */
int main(int argc, char* argv[]) {
    try {
        if (argc != 7) throw std::invalid_argument("Expected six arguments");
        flight::Config config{argv[1], integer(argv[2]), integer(argv[3]), integer(argv[4]), integer(argv[5]), integer(argv[6])};
        emit(flight::simulate(config));
        return 0;
    } catch (const std::exception&) {
        std::cerr << "Invalid testbed arguments or unavailable result\n";
        return 2;
    }
}
