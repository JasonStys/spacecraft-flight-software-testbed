"""Actual frozen-executable export and loopback smoke test by Jason Stys.

Functions: main, read_output. Variables: process, queue, temporary output, HTTP responses.
Line inventory: docs/CODE_INDEX.md. Starts/stops only the explicitly supplied owned bundle.
"""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path


def main(executable: Path) -> None:
    """Verify packaged C++ worker/resources, health, scenario API and real built HTML/JS."""
    executable = executable.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="flight-smoke-") as temporary:
        output = Path(temporary) / "evidence.json"
        subprocess.run(
            [str(executable), "export", "--scenario", "nominal", "--output", str(output)],
            check=True,
            timeout=30,
        )
        assert json.loads(output.read_bytes())["provenance"]["clock"] == "logical ticks"
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read child stdout without a blocking readline in the timeout-owning main thread."""
        assert process.stdout is not None
        for line in process.stdout:
            lines.put(line.strip())

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        url = ""
        for _ in range(5):
            line = lines.get(timeout=15)
            if line.startswith("http://127.0.0.1:"):
                url = line
                break
        assert url, "Frozen server did not announce a loopback URL"
        with urllib.request.urlopen(url + "api/health", timeout=5) as response:
            assert json.loads(response.read())["status"] == "ok"
        with urllib.request.urlopen(url, timeout=5) as response:
            html = response.read().decode()
            assert "Spacecraft Flight Software Testbed" in html and "/assets/" in html
        with urllib.request.urlopen(
            url + "api/run?scenario=watchdog-hang&duration=240", timeout=5
        ) as response:
            assert json.loads(response.read())["summary"]["resets"] == 1
        print("Frozen app: C++ executive export, web assets, health and scenario API passed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=3)
        if process.stdout:
            process.stdout.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
