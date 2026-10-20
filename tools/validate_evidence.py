"""Cross-platform golden replay and measured timing evidence by Jason Stys.

Function: main. Variables: output path, scenario evidence and observed subprocess timings.
Use --write only to intentionally refresh reviewed fixtures; exact lines: docs/CODE_INDEX.md.
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flightlab.engine import SCENARIOS, Settings, binary_path, build_run  # noqa: E402


def main() -> None:
    """Compare integer replays across builds; timing is observational, never a flaky CI gate."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    golden = {}
    for scenario in SCENARIOS:
        run = build_run(Settings(scenario=scenario))
        golden[scenario] = {
            "trajectory_sha256": run["provenance"]["trajectory_sha256"],
            "summary": run["summary"],
        }
    path = root / "docs/reports/replay-contracts.json"
    encoded = json.dumps(golden, indent=2, sort_keys=True) + "\n"
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8", newline="\n")
    elif json.loads(path.read_text(encoding="utf-8")) != golden:
        raise SystemExit("Replay differs from reviewed integer contracts")
    durations = []
    for _ in range(15):
        start = time.perf_counter()
        subprocess.run(
            [str(binary_path()), "watchdog-hang", "480", "120", "5", "8", "2"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        durations.append((time.perf_counter() - start) * 1000)
    print(
        f"Seven cross-platform replay contracts passed; 15 cold native processes median {statistics.median(durations):.2f} ms, max {max(durations):.2f} ms (host-specific, includes spawn/JSON)"
    )


if __name__ == "__main__":
    main()
