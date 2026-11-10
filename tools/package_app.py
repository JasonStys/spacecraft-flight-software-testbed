"""Build and verify versioned portable applications by Jason Stys.

Function: main. Variables: config, source metadata, fixed worker and owned extraction directory.
Only the actual extracted binary is accepted. Exact lines: docs/CODE_INDEX.md. No installer hooks.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

if __package__:
    from .portable_archive import archive_metadata, create_archive, extract_archive
    from .release_contract import ROOT, asset_paths, configuration, require, source_metadata
else:
    from portable_archive import archive_metadata, create_archive, extract_archive
    from release_contract import ROOT, asset_paths, configuration, require, source_metadata


def main() -> int:
    """Build from pinned dependencies, preserve native archive semantics, then exercise extracted UI."""
    parser = argparse.ArgumentParser(
        description="Build and test this platform's portable application"
    )
    parser.add_argument("--output-root", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    config, metadata = configuration(), source_metadata()
    require((ROOT / "web/dist/index.html").is_file(), "Build production web assets first")
    generated = ROOT / ".runtime/package-meta"
    generated.mkdir(parents=True, exist_ok=True)
    identity = generated / "RELEASE.json"
    identity.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    executable_name = config["executable"]
    worker = ROOT / (
        "native-build/Release/flight_core.exe"
        if sys.platform == "win32"
        else "native-build/flight_core"
    )
    require(worker.is_file(), "Build the fixed native worker first")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        executable_name,
        "--add-data",
        "web/dist:web/dist",
        "--add-binary",
        str(worker) + ":native",
        "--add-data",
        "flightlab/resources:flightlab/resources",
        "--add-data",
        str(identity) + ":flightlab/resources",
        "--add-data",
        "LICENSE:licenses/project",
        "--add-data",
        "licenses/PYTHON.txt:licenses/python",
        "--add-data",
        "docs/THIRD_PARTY.md:docs",
    ]
    installed = distribution("pyinstaller")
    notices = [
        installed.locate_file(path)
        for path in (installed.files or [])
        if str(path).endswith("licenses/COPYING.txt")
    ]
    require(len(notices) == 1, "Expected the pinned PyInstaller distribution license")
    command.extend(["--add-data", str(notices[0]) + ":licenses/pyinstaller", "launcher.py"])
    subprocess.run(command, cwd=ROOT, check=True, timeout=600)
    bundle = ROOT / "dist" / executable_name
    shutil.copyfile(identity, bundle / "RELEASE.json")
    archive, checksum = asset_paths(metadata)
    archive, checksum = (
        args.output_root.resolve() / archive.name,
        args.output_root.resolve() / checksum.name,
    )
    archive.parent.mkdir(parents=True, exist_ok=True)
    require(not checksum.exists(), "Checksum destination already exists")
    create_archive(bundle, archive)
    require(
        archive_metadata(archive, executable_name) == metadata, "Created archive identity mismatch"
    )
    with tempfile.TemporaryDirectory(prefix="flight-extracted-") as temporary:
        extracted = extract_archive(archive, Path(temporary) / "unpacked", executable_name)
        executable = extracted / (executable_name + (".exe" if sys.platform == "win32" else ""))
        subprocess.run(
            [sys.executable, str(ROOT / "tools/smoke_app.py"), str(executable)],
            cwd=temporary,
            check=True,
            timeout=120,
        )
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Extracted portable application passed: {archive.name} SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
