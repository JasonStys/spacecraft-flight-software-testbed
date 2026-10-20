"""Independent executive, failure-boundary and replay contracts by Jason Stys.

Functions: test_*; variables: complete scenario grid, event deadlines and serialized worker fixtures.
Exact definition and variable lines: docs/CODE_INDEX.md. No native implementation is imported.
"""

import copy
import json
import subprocess
from dataclasses import asdict
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from flightlab.engine import (
    CHOICES,
    SCENARIOS,
    Settings,
    binary_path,
    build_run,
    catalog,
    execute,
    run_id,
    validate_worker,
)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenarios(scenario):
    """Check expected deadlines, loss and nominal arithmetic independently of C++ internals."""
    run = build_run(Settings(scenario=scenario))
    rows = run["experiment"]["samples"]
    summary = run["summary"]
    assert run["id"] == run_id(run)
    assert len(rows) == 241 and rows[10]["mode"] == "SCIENCE"
    assert run["reference"]["samples"][-1]["payloads"] == len(range(10, 230, 2))
    assert rows[160]["mode"] == "SCIENCE" and rows[-1]["mode"] == "STANDBY"
    assert summary["duplicates"] == 1
    if scenario == "watchdog-hang":
        assert rows[123]["boot"] == 1 and rows[124]["boot"] == 2
        assert rows[126]["mode"] == "SAFE" and rows[159]["mode"] == "SAFE"
        assert summary["unserviced"] == 1
        # Last completed checkpoint before the hang is tick 112, science every second tick.
        assert rows[124]["payloads"] == len(range(10, 113, 2))
        assert summary["lost_payloads"] == len(range(114, 120, 2))
    elif scenario == "sensor-stale":
        assert rows[124]["mode"] == "SCIENCE" and rows[125]["mode"] == "SAFE"
        assert rows[135]["sensor_age"] == 16 and rows[136]["sensor_age"] == 0
        assert rows[159]["mode"] == "SAFE"
    elif scenario == "checkpoint-corrupt":
        assert rows[120]["payloads"] == 0 and rows[120]["boot"] == 2
        assert summary["lost_payloads"] == len(range(10, 120, 2))
        assert any(e["type"] == "checkpoint-rejected" for e in run["experiment"]["events"])
    elif scenario == "brownout":
        assert rows[120]["mode"] == rows[159]["mode"] == "SAFE"
        assert rows[131]["power_score"] == 200 and rows[132]["power_score"] == 900
    elif scenario == "telemetry-gap":
        assert [r["tick"] for r in rows if not r["delivered"]] == list(range(120, 132))
        assert summary["payloads"] == summary["reference_payloads"]
    elif scenario == "command-corrupt":
        assert summary["rejected"] == 1 and rows[-1]["accepted"] == 3
    else:
        assert summary["payloads"] == 110 and summary["safe_ticks"] == 0
    assert summary["resets"] == (1 if scenario in {"watchdog-hang", "checkpoint-corrupt"} else 0)


@given(
    st.sampled_from(list(SCENARIOS)),
    st.sampled_from(CHOICES["duration"]),
    st.sampled_from(CHOICES["fault_tick"]),
    st.sampled_from(CHOICES["watchdog"]),
    st.sampled_from(CHOICES["checkpoint_period"]),
    st.sampled_from(CHOICES["sample_period"]),
)
@hypothesis_settings(max_examples=40, deadline=None)
def test_replay_properties(scenario, duration, fault, watchdog, checkpoint, sampling):
    """Seed-independent property exploration preserves invariants and detached cache results."""
    selected = Settings(scenario, duration, fault, watchdog, checkpoint, sampling)
    run = build_run(selected)
    assert run == build_run(selected)
    for tick, row in enumerate(run["experiment"]["samples"]):
        assert tick == row["tick"] == row["sequence"]
        assert 0 <= row["committed"] <= row["payloads"] <= duration // sampling
        assert row["boot"] in (1, 2) and 0 <= row["watchdog_age"] <= watchdog
    run["experiment"]["samples"][0]["payloads"] = 9999
    assert build_run(selected)["experiment"]["samples"][0]["payloads"] == 0


@pytest.mark.parametrize(
    "key,value",
    [
        ("scenario", "unknown"),
        ("scenario", []),
        ("duration", True),
        ("duration", 240.0),
        ("fault_tick", 0),
        ("watchdog", 0),
        ("checkpoint_period", 3),
        ("sample_period", -1),
    ],
)
def test_invalid_settings(key, value):
    """Strict primitive types prevent bool/numeric coercion and unbounded workloads."""
    with pytest.raises(ValueError):
        Settings(**{key: value})


def test_catalog_and_binary(monkeypatch, tmp_path):
    """Public defaults are serializable; frozen worker lookup remains a fixed owned path."""
    assert catalog()["defaults"] == asdict(Settings())
    monkeypatch.setattr("flightlab.engine.sys.frozen", True, raising=False)
    monkeypatch.setattr("flightlab.engine.sys._MEIPASS", str(tmp_path), raising=False)
    assert binary_path().parent == tmp_path / "native"


@pytest.mark.parametrize(
    "mutation", ["envelope", "grid", "frame", "value", "sequence", "progress", "events", "event"]
)
def test_worker_schema(mutation):
    """Malformed native output is refused rather than silently presented as reliable evidence."""
    selected = Settings()
    data = copy.deepcopy(build_run(selected)["experiment"])
    if mutation == "envelope":
        data = []
    elif mutation == "grid":
        data["samples"].pop()
    elif mutation == "frame":
        data["samples"][0]["extra"] = 1
    elif mutation == "value":
        data["samples"][0]["delivered"] = 1
    elif mutation == "sequence":
        data["samples"][0]["sequence"] = 99
    elif mutation == "progress":
        data["samples"][0]["committed"] = 1
    elif mutation == "events":
        data["events"] = []
    else:
        data["events"][0]["type"] = "<script>"
    with pytest.raises(RuntimeError):
        validate_worker(data, selected)


@pytest.mark.parametrize("failure", ["timeout", "exit", "json", "large", "schema"])
def test_worker_failure(failure):
    """Timeout/nonzero/oversize/malformed outputs have explicit controlled error paths."""
    execute.cache_clear()
    output = (
        b"{}" if failure == "schema" else b"x" * 2_000_001 if failure == "large" else b"invalid"
    )
    result = subprocess.CompletedProcess([], 0, stdout=output)
    error = (
        subprocess.TimeoutExpired([], 5)
        if failure == "timeout"
        else subprocess.CalledProcessError(2, [])
        if failure == "exit"
        else None
    )
    with patch("flightlab.engine.subprocess.run", side_effect=error, return_value=result):
        with pytest.raises(RuntimeError):
            execute(Settings(), "test-" + failure)
    execute.cache_clear()


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["unknown", "240", "120", "5", "8", "2"],
        ["nominal", "240x", "120", "5", "8", "2"],
        ["nominal", "999999999999999999", "120", "5", "8", "2"],
    ],
)
def test_native_cli_invalid(arguments):
    """Actual native argument parser refuses partial numbers, overflow and missing arguments."""
    result = subprocess.run([str(binary_path()), *arguments], capture_output=True, timeout=5)
    assert result.returncode == 2 and not result.stdout


def test_cross_process_determinism():
    """Fresh worker processes produce byte-identical evidence, independent of cache use."""
    command = [str(binary_path()), "watchdog-hang", "240", "120", "5", "8", "2"]
    first = subprocess.run(command, capture_output=True, check=True, timeout=5).stdout
    second = subprocess.run(command, capture_output=True, check=True, timeout=5).stdout
    assert first == second and json.loads(first)["samples"][124]["boot"] == 2
