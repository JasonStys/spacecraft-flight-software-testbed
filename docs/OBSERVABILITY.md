# Review recovery observability

The full-run audit compares known synthetic onboard changes with received downlink witnesses. It covers mode/boot changes and increases in rejected, duplicate, unserviced-command and volatile-loss counters. It is independent of the replay cursor and perspective; the ordinary received-only replay still never substitutes missing frames with onboard truth.

A mode must be received before that mode changes again to count as confirmed. A boot change can be confirmed by a later received frame in that boot. A cumulative counter confirms **at least that value**, possibly after later increments; it does not identify the exact unseen increment time. Search stops at a later boot. No confirming packet means not observed before the relevant mode/boot/window boundary, not proof nothing happened. A short BOOT or SAFE episode can occur entirely between packets.

Each item retains the exact onboard tick, first received confirmation, last received tick before the known change and confirmation delay. The received bounds can include hidden intermediate states; they are not reconstructed exact transition timestamps. JSON/HTML and immutable CLI history include the same run-hashed audit. The underlying replay hash, native command/watchdog/checkpoint rules and events remain unchanged.

Everything is software-only and synthetic. SAFE is a state label, not physical assurance. No real flight controller, guidance/targeting or hardware adapter is added.
