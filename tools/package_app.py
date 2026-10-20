"""Build portable native bundles from reviewed source by Jason Stys.

Function: main. Variables: root, slug, executable, PyInstaller command, zip manifest.
Generated bundles are unsigned; exact symbols: docs/CODE_INDEX.md. No installer/elevation.
"""

import hashlib
import platform
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path


def main() -> int:
    """Freeze the existing production web build, smoke it, then zip this platform's bundle."""
    root = Path(__file__).resolve().parents[1]
    if not (root / "web/dist/index.html").is_file():
        raise SystemExit("Run npm ci and npm run build first")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "SpacecraftFlightTestbed",
        "--add-data",
        "web/dist:web/dist",
        "--add-binary",
        str(
            root
            / (
                "native-build/Release/flight_core.exe"
                if sys.platform == "win32"
                else "native-build/flight_core"
            )
        )
        + ":native",
        "--add-data",
        "flightlab/resources:flightlab/resources",
        "--add-data",
        "LICENSE:licenses/project",
        "--add-data",
        "licenses/PYTHON.txt:licenses/python",
        "--add-data",
        "docs/THIRD_PARTY.md:docs",
        "launcher.py",
    ]
    distribution_info = distribution("pyinstaller")
    notices = [
        distribution_info.locate_file(path)
        for path in (distribution_info.files or [])
        if str(path).endswith("licenses/COPYING.txt")
    ]
    if len(notices) != 1:
        raise SystemExit("Expected the locked PyInstaller distribution license")
    command[command.index("launcher.py") : command.index("launcher.py")] = [
        "--add-data",
        str(notices[0]) + ":licenses/pyinstaller",
    ]
    subprocess.run(command, cwd=root, check=True, timeout=600)
    executable = (
        root
        / "dist/SpacecraftFlightTestbed"
        / ("SpacecraftFlightTestbed.exe" if sys.platform == "win32" else "SpacecraftFlightTestbed")
    )
    subprocess.run(
        [sys.executable, "tools/smoke_app.py", str(executable)], cwd=root, check=True, timeout=90
    )
    slug = f"spacecraft-flight-software-testbed-{platform.system().lower()}-{platform.machine().lower()}"
    archive = Path(
        shutil.make_archive(
            str(root / "dist" / slug), "zip", root / "dist", "SpacecraftFlightTestbed"
        )
    )
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    (root / "dist" / f"{slug}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Portable bundle verified: {archive.name} SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
