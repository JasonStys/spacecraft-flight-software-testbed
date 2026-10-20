"""Local website launcher and reproducible export CLI by Jason Stys.

Functions: main. Variables: parsed CLI arguments, server, output evidence.
Exact definition/variable lines are generated in docs/CODE_INDEX.md.
"""

import argparse
import sqlite3
import sys
import webbrowser
from pathlib import Path

from flightlab.engine import CHOICES, SCENARIOS, Settings, build_run
from flightlab.reports import export_report, save_history
from flightlab.server import make_server


def main(argv: list[str] | None = None) -> int:
    """Serve loopback or export reviewed evidence; never overwrite an existing export."""
    parser = argparse.ArgumentParser(description="Spacecraft Flight Software Testbed by Jason Stys")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Launch the local website")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--no-browser", action="store_true")
    export = commands.add_parser("export", help="Save deterministic evidence")
    export.add_argument("--scenario", choices=SCENARIOS, default="nominal")
    for key, choices in CHOICES.items():
        export.add_argument(
            "--" + key,
            type=int,
            choices=choices,
            default=getattr(Settings(), key),
        )
    export.add_argument("--format", choices=("json", "csv", "html"), default="json")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--history", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            run = build_run(Settings(**{key: getattr(args, key) for key in ("scenario", *CHOICES)}))
            body, _ = export_report(run, args.format)
            # History and export are separate destinations, never claim cross-file atomicity.
            if args.output.exists():
                raise FileExistsError("Export destination already exists")
            if args.history:
                save_history(args.history, run)
            with args.output.open("xb") as destination:
                destination.write(body)
            print(f"Saved {run['id']}")
            return 0
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        assets = root / "web" / "dist"
        if not (assets / "index.html").is_file():
            raise OSError("Website build missing. Run npm ci and npm run build first.")
        with make_server(assets, args.port) as server:
            url = f"http://127.0.0.1:{server.server_port}/"
            print(f"Spacecraft Flight Software Testbed by Jason Stys\n{url}", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever(poll_interval=0.25)
            except KeyboardInterrupt:
                print("Workbench stopped.", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"Cannot complete operation: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
