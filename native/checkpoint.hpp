/* Canonical teaching checkpoint codec by Jason Stys. NOT a flight or secure-storage format.
 * Types/functions: Progress, Checkpoint, crc32, encode_checkpoint, decode_checkpoint.
 * Variables: bounded progress, little-endian bytes and checksum; exact lines: docs/CODE_INDEX.md.
 */
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace flight {
/** Monotonic command high-water mark and working science count; snapshots may lag live work. */
struct Progress {
    std::uint32_t last_command = 0;
    std::uint32_t payloads = 0;
    bool operator==(const Progress&) const = default;
};
using Checkpoint = std::array<std::uint8_t, 20>;
inline constexpr std::uint32_t progress_limit = 1'000'000;
/** CRC-32/ISO-HDLC for accidental-corruption detection, never cryptographic authentication. */
std::uint32_t crc32(std::span<const std::uint8_t> bytes);
/** Encode bounded progress as magic/version/reserved/command/payload/CRC in explicit LE order. */
Checkpoint encode_checkpoint(Progress progress);
/** Reject wrong length, version, reserved bits, CRC and bounds without unsafe buffer reads. */
std::optional<Progress> decode_checkpoint(std::span<const std::uint8_t> bytes);
} // namespace flight
