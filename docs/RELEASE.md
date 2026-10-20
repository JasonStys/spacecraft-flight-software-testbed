# Release, operation and rollback

By Jason Stys. Portable bundles are unsigned, software-only and not flight qualified.

## Build and preflight

1. Use reviewed source, supported Python/Node and compiler; install development lockfiles with hashes. Build native tests and production web assets.
2. Run the complete lint/type/unit/property/HTTP/browser/golden replay gates. Confirm CI's ASan/UBSan, coverage, security analysis, audits and all3OS bundle smoke jobs pass on the exact commit. Check account Actions storage; no automatic deletion or cleanup is authorized by these tools.
3. Run `python tools/package_app.py` on the target OS. It bundles the fixed worker, built assets, SQL resources and project/CPython/PyInstaller notices. Before ZIP creation it actually launches the frozen executable, exports evidence, starts its loopback service, exercises health/scenario APIs and checks real web assets.
4. `python tools/smoke_app.py path/to/SpacecraftFlightTestbed` repeats the owned bundle smoke; the test stops only its child server.

## GitHub release workflow

Dispatch **Portable release** from main with a new digits.digits.digits version. `prepare_release.py` requires successful Validation/CodeQL workflow runs for GITHUB_SHA; it refuses malformed version input. A new draft release is created at that SHA. Three OS jobs independently build/test/package, and `upload_release.py` refuses public/non-draft release targets or unexpected files. Exactly one ZIP/SHA256 pair per job is uploaded directly to the draft; no Actions artifact/cache uploads.

Before publishing: ensure all jobs passed; inspect the six expected assets, download and verify each checksum; smoke the newly downloaded matching local OS bundle. Record workflow/source/release links in validation evidence. Publish the draft only after review. Release assets are not Actions artifacts. Do not overwrite a published asset or reuse a release version to hide changes. Tools fail closed rather than silently replace binaries.

## Operate

Extract the entire OS-matching bundle, then launch its executable with `serve` (the launcher defaults to serve when no arguments). It opens a loopback URL in the default browser. `serve --no-browser` prints the URL without opening a tab. The process stays in the console; Ctrl+C stops it. There is no installation service, background task, cloud login, real telemetry source, networking to a device or OS security change. Keep the folder together; moving only the executable breaks packaged resource discovery.

## Rollback

If reports diverge, the app crashes, a trust problem is suspected or checks regress: stop the local app, preserve synthetic evidence, mark the affected release unsuitable in its notes, and use a previously reviewed release/source version. Do not mutate or delete user history. Use a new database/export destination for a schema change; version data explicitly. There is no real spacecraft/production control system to roll back, no remote user migration and no destructive uninstall step. Delete/extract folders only under the user's normal file-management decisions.
