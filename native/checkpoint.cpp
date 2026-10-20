/* Bounded portable checkpoint serialization by Jason Stys.
 * Functions: put32, get32, crc32, encode_checkpoint, decode_checkpoint.
 * Variables: byte offsets, polynomial, CRC and progress. Exact lines: docs/CODE_INDEX.md.
 */
#include "checkpoint.hpp"
#include <stdexcept>

namespace flight {
namespace {
/** Store a 32-bit value at an internal validated offset, independent of host endianness. */
void put32(Checkpoint& bytes, std::size_t offset, std::uint32_t value) {
    for (std::size_t i = 0; i < 4; ++i)
        bytes[offset + i] = static_cast<std::uint8_t>((value >> (8 * i)) & 0xffU);
}
/** Load a 32-bit value only after the public decoder has checked the full 20-byte length. */
std::uint32_t get32(std::span<const std::uint8_t> bytes, std::size_t offset) {
    std::uint32_t value = 0;
    for (std::size_t i = 0; i < 4; ++i) value |= std::uint32_t{bytes[offset + i]} << (8 * i);
    return value;
}
} // namespace

/** Use the standard reflected CRC polynomial, initial/final XOR, and eight bit rounds per byte. */
std::uint32_t crc32(std::span<const std::uint8_t> bytes) {
    std::uint32_t crc = 0xffffffffU;
    for (auto byte : bytes) {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1U) ^ ((crc & 1U) ? 0xedb88320U : 0U);
    }
    return crc ^ 0xffffffffU;
}

/** Serialize fields explicitly; no struct padding, pointer casts or ABI-dependent image dumps. */
Checkpoint encode_checkpoint(Progress progress) {
    if (progress.last_command > progress_limit || progress.payloads > progress_limit)
        throw std::invalid_argument("Progress outside teaching format bounds");
    Checkpoint bytes{};
    put32(bytes, 0, 0x42545346U); // ASCII FSTB, little endian.
    bytes[4] = 1; // Version 1; bytes 5..7 reserved and zero.
    put32(bytes, 8, progress.last_command);
    put32(bytes, 12, progress.payloads);
    put32(bytes, 16, crc32(std::span<const std::uint8_t>{bytes}.first(16)));
    return bytes;
}

/** Validate framing before any offset access; CRC is corruption detection, not a trust boundary. */
std::optional<Progress> decode_checkpoint(std::span<const std::uint8_t> bytes) {
    if (bytes.size() != 20) return std::nullopt;
    if (get32(bytes, 0) != 0x42545346U || bytes[4] != 1 || bytes[5] || bytes[6] || bytes[7])
        return std::nullopt;
    if (get32(bytes, 16) != crc32(bytes.first(16))) return std::nullopt;
    Progress progress{get32(bytes, 8), get32(bytes, 12)};
    if (progress.last_command > progress_limit || progress.payloads > progress_limit)
        return std::nullopt;
    return progress;
}
} // namespace flight
