"""Synthetic executive recovery observability review by Jason Stys.

Function: observability. Variables: onboard state/counter changes and bounded received witnesses.
Known simulator truth remains separate from downlink evidence. Exact lines: docs/CODE_INDEX.md.
"""

from typing import Any


def observability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare onboard changes with first confirming received frame, without inventing timing.

    A brief mode that changes again before reception is unobserved. Counter confirmations mean
    at least the reported value was received, not the exact instant of the increment. Search
    stops on a later boot. Bounds describe received evidence, not unseen intermediate behavior.
    """
    result = []
    for index, row in enumerate(rows[1:], 1):
        previous = rows[index - 1]
        for field in ("mode", "boot", "rejected", "duplicates", "unserviced", "lost_payloads"):
            if row[field] == previous[field] or (
                field not in {"mode", "boot"} and row[field] < previous[field]
            ):
                continue
            confirmation = None
            for candidate in rows[index:]:
                if candidate["boot"] != row["boot"]:
                    break
                if field in {"mode", "boot"} and candidate[field] != row[field]:
                    break
                if candidate["delivered"] and (
                    candidate[field] == row[field]
                    if field in {"mode", "boot"}
                    else candidate[field] >= row[field]
                ):
                    confirmation = candidate["tick"]
                    break
            last_received = next(
                (p["tick"] for p in reversed(rows[:index]) if p["delivered"]), None
            )
            result.append(
                {
                    "field": field,
                    "before": previous[field],
                    "after": row[field],
                    "onboard_tick": row["tick"],
                    "received_confirmation_tick": confirmation,
                    "last_received_before_change": last_received,
                    "confirmation_delay_ticks": confirmation - row["tick"]
                    if confirmation is not None
                    else None,
                    "status": "received-confirmation"
                    if confirmation is not None
                    else "not-observed-in-window",
                }
            )
    return result
