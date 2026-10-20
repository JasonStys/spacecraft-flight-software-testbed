"""Bounded native worker bridge and deterministic evidence by Jason Stys.

Classes/functions: Settings, catalog, execute, build_run, run_id. Variables: choices, schemas,
worker fingerprint and immutable cached JSON. Exact source inventory: docs/CODE_INDEX.md.
"""

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

SCENARIOS = {
    "nominal": "Healthy executive and a deliberate duplicate command",
    "watchdog-hang": "Hung task, independent watchdog reset and checkpoint restore",
    "sensor-stale": "Stale sensor, latched SAFE mode and explicit healthy resume",
    "telemetry-gap": "Twelve missing downlink frames; onboard work continues",
    "checkpoint-corrupt": "Invalid checkpoint CRC, reset to empty progress",
    "brownout": "Synthetic low-power index inhibits science and checkpointing",
    "command-corrupt": "Bad command CRC rejected without advancing its high-water mark",
}
CHOICES = {
    "duration": (240, 480),
    "fault_tick": (80, 120, 160),
    "watchdog": (3, 5, 8),
    "checkpoint_period": (4, 8, 16),
    "sample_period": (2, 4),
}
FIELDS = (
    "tick",
    "uptime",
    "boot",
    "mode",
    "sensor_age",
    "sensor_value",
    "sensor_valid",
    "power_score",
    "payloads",
    "committed",
    "lost_payloads",
    "accepted",
    "rejected",
    "duplicates",
    "unserviced",
    "watchdog_age",
    "sequence",
    "delivered",
    "fault_active",
)
EVENTS = {
    "initial-boot",
    "fault-injected",
    "checkpoint-restored",
    "checkpoint-rejected",
    "integrity-reset",
    "watchdog-reset",
    "boot-complete-safe",
    "boot-complete-standby",
    "power-low",
    "sensor-stale",
    "command-accepted",
    "command-rejected",
    "command-duplicate",
    "command-unserviced",
    "checkpoint-saved",
}


@dataclass(frozen=True)
class Settings:
    """Finite reviewed fixture choices; bools, floats and arbitrary workloads are refused."""

    scenario: str = "nominal"
    duration: int = 240
    fault_tick: int = 120
    watchdog: int = 5
    checkpoint_period: int = 8
    sample_period: int = 2

    def __post_init__(self) -> None:
        """Validate before subprocess launch, keeping both runtime and output size bounded."""
        if type(self.scenario) is not str or self.scenario not in SCENARIOS:
            raise ValueError("Unknown scenario")
        for key, choices in CHOICES.items():
            value = getattr(self, key)
            if type(value) is not int or value not in choices:
                raise ValueError(f"Unsupported {key}")


def catalog() -> dict[str, Any]:
    """Return public scenario descriptions, allowed integer settings and defaults."""
    return {"scenarios": SCENARIOS, "choices": CHOICES, "defaults": asdict(Settings())}


def binary_path() -> Path:
    """Resolve only the trusted built worker beside source or inside the frozen bundle."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    suffix = ".exe" if sys.platform == "win32" else ""
    folder = (
        "native"
        if getattr(sys, "frozen", False)
        else ("native-build/Release" if sys.platform == "win32" else "native-build")
    )
    return root / folder / ("flight_core" + suffix)


def canonical(value: Any) -> bytes:
    """Canonical UTF-8 evidence encoding; no nonfinite numeric JSON is permitted."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def run_id(run: dict[str, Any]) -> str:
    """Identify the entire evidence payload except its self-referential id field."""
    return hashlib.sha256(canonical({k: v for k, v in run.items() if k != "id"})).hexdigest()


def validate_worker(data: Any, settings: Settings) -> dict[str, Any]:
    """Treat native output as untrusted: bound every field, event, row count and grid."""
    if not isinstance(data, dict) or set(data) != {"samples", "events"}:
        raise RuntimeError("Invalid worker envelope")
    rows, events = data["samples"], data["events"]
    if not isinstance(rows, list) or len(rows) != settings.duration + 1:
        raise RuntimeError("Invalid worker grid")
    bool_fields = {"sensor_valid", "delivered", "fault_active"}
    for tick, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(FIELDS):
            raise RuntimeError("Invalid worker frame")
        for key, value in row.items():
            valid = (
                type(value) is bool
                if key in bool_fields
                else type(value) is str and value in {"BOOT", "STANDBY", "SCIENCE", "SAFE"}
                if key == "mode"
                else type(value) is int and 0 <= value <= 1000
            )
            if not valid:
                raise RuntimeError("Invalid worker value")
        if row["tick"] != tick or row["sequence"] != tick or not 1 <= row["boot"] <= 2:
            raise RuntimeError("Invalid worker sequence")
        if row["committed"] > row["payloads"] or row["uptime"] > tick:
            raise RuntimeError("Invalid worker progress")
    if not isinstance(events, list) or not 1 <= len(events) <= settings.duration + 32:
        raise RuntimeError("Invalid worker events")
    previous = -1
    for event in events:
        if (
            not isinstance(event, dict)
            or set(event) != {"tick", "type", "value"}
            or type(event["tick"]) is not int
            or not previous <= event["tick"] <= settings.duration
            or type(event["type"]) is not str
            or event["type"] not in EVENTS
            or type(event["value"]) is not int
            or not 0 <= event["value"] <= 1000
        ):
            raise RuntimeError("Invalid worker event")
        previous = event["tick"]
    return data


@lru_cache(maxsize=32)
def execute(settings: Settings, fingerprint: str) -> bytes:
    """Run a fixed executable without a shell; cache serialized evidence, not mutable objects."""
    del fingerprint  # Cache namespace changes whenever the worker bytes change.
    command = [str(binary_path()), settings.scenario, *(str(getattr(settings, k)) for k in CHOICES)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=5, check=True)
        if len(result.stdout) > 2_000_000:
            raise RuntimeError("Worker output too large")
        return canonical(validate_worker(json.loads(result.stdout), settings))
    except (subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError("Worker failed; rebuild the trusted native core") from error


def build_run(settings: Settings) -> dict[str, Any]:
    """Compare the selected fault against an identical-setting nominal deterministic replay."""
    with binary_path().open("rb") as source:
        fingerprint = hashlib.file_digest(source, "sha256").hexdigest()
    experiment = json.loads(execute(settings, fingerprint))
    reference_settings = Settings(**(asdict(settings) | {"scenario": "nominal"}))
    reference = json.loads(execute(reference_settings, fingerprint))
    rows = experiment["samples"]
    last = rows[-1]
    run = {
        "schema": 1,
        "scenario": settings.scenario,
        "settings": asdict(settings),
        "experiment": experiment,
        "reference": reference,
        "summary": {
            "resets": last["boot"] - 1,
            "lost_payloads": last["lost_payloads"],
            "payloads": last["payloads"],
            "committed": last["committed"],
            "reference_payloads": reference["samples"][-1]["payloads"],
            "missing_frames": sum(not row["delivered"] for row in rows),
            "safe_ticks": sum(row["mode"] == "SAFE" for row in rows),
            "max_sensor_age": max(row["sensor_age"] for row in rows),
            "rejected": last["rejected"],
            "duplicates": last["duplicates"],
            "unserviced": last["unserviced"],
        },
        "provenance": {
            "author": "Jason Stys",
            "version": "1.0.0",
            "clock": "logical ticks",
            "worker_sha256": fingerprint,
            "trajectory_sha256": hashlib.sha256(canonical(experiment)).hexdigest(),
            "units": "Synthetic sensor/power indexes and integer counters; no physical units",
            "scope": "Original software-only teaching executive; not flight qualified or real time",
        },
    }
    run["id"] = run_id(run)
    return run
