"""Independent synthetic state/downlink witness traces by Jason Stys.

Functions: frame and test_*; variables: hidden short modes, persistent counters and boot boundaries.
No received confirmation is promoted into an exact unseen transition time. Lines: docs/CODE_INDEX.md.
"""

from typing import Any

from flightlab.engine import Settings, build_run
from flightlab.observability import observability


def frame(
    tick: int, mode: str, delivered: bool, boot: int = 1, rejected: int = 0
) -> dict[str, Any]:
    """Construct only the independent minimal state/counter/downlink contract for this review."""
    return {
        "tick": tick,
        "mode": mode,
        "delivered": delivered,
        "boot": boot,
        "rejected": rejected,
        "duplicates": 0,
        "unserviced": 0,
        "lost_payloads": 0,
    }


def test_hidden_modes_counter_threshold_and_reset_boundary():
    """A brief SAFE/BOOT state can be unseen even when a later cumulative counter is received."""
    rows = [
        frame(0, "SCIENCE", True),
        frame(1, "SAFE", False, rejected=1),
        frame(2, "SCIENCE", False, rejected=1),
        frame(3, "SCIENCE", True, rejected=2),
        frame(4, "BOOT", False, 2),
        frame(5, "SAFE", True, 2),
        frame(6, "SCIENCE", False, 2),
        frame(7, "SCIENCE", False, 2),
    ]
    result = observability(rows)
    hidden = next(item for item in result if item["field"] == "mode" and item["onboard_tick"] == 1)
    assert hidden["received_confirmation_tick"] is None
    count = next(
        item for item in result if item["field"] == "rejected" and item["onboard_tick"] == 1
    )
    assert count["received_confirmation_tick"] == 3 and count["confirmation_delay_ticks"] == 2
    assert count["last_received_before_change"] == 0
    boot = next(item for item in result if item["field"] == "boot")
    assert boot["received_confirmation_tick"] == 5
    last = next(item for item in result if item["field"] == "mode" and item["onboard_tick"] == 6)
    assert last["status"] == "not-observed-in-window"


def test_absent_previous_downlink_and_no_changes():
    """An unknown preceding observation stays null; an empty/constant trace invents no events."""
    assert observability([]) == []
    assert observability([frame(0, "SCIENCE", True), frame(1, "SCIENCE", True)]) == []
    row = observability([frame(0, "SCIENCE", False), frame(1, "SAFE", True)])[0]
    assert row["last_received_before_change"] is None
    assert row["confirmation_delay_ticks"] == 0
    reset = observability(
        [
            frame(0, "SCIENCE", True),
            frame(1, "SCIENCE", False, rejected=1),
            frame(2, "BOOT", False, boot=2),
            frame(3, "BOOT", True, boot=2),
        ]
    )
    old_counter = next(item for item in reset if item["field"] == "rejected")
    assert old_counter["received_confirmation_tick"] is None


def test_native_reset_and_cumulative_rejection_have_real_witnesses():
    """Native reset witnesses and received confirmation times are consistent with actual delivered rows."""
    for scenario in ("watchdog-hang", "checkpoint-corrupt", "command-corrupt", "telemetry-gap"):
        run = build_run(Settings(scenario=scenario))
        for item in run["observability"]:
            tick = item["received_confirmation_tick"]
            if tick is not None:
                observed = run["experiment"]["samples"][tick]
                assert observed["delivered"] and tick >= item["onboard_tick"]
        assert run["provenance"]["trajectory_sha256"]
