# Portable release refresh validation — 2026-11-09

By Jason Stys. Version 1.1.0 prepares the current recovery-observability workflow for new portable downloads; historical 1.0.0 downloads are unchanged.

## Recorded local results

On Windows/Python 3.14.6, 151 Python tests passed with 99.53% combined statement/branch coverage against the unchanged 90% requirement. Seventy new cases exercise release identity, immutable draft/tag rules, failed/incomplete/ambiguous prerequisite histories, checksum/archive/source mismatch, path/link escape and frozen package metadata. GitHub replies are independent fixtures; these tests perform no GitHub writes. The package metadata and HTTP modules reached 100% coverage.

The unchanged native executive passed its three build contracts. All seven original deterministic trajectory hashes and scenario summaries remain unchanged. Twelve TypeScript tests, strict production build, Ruff and strict mypy passed. All 24 separate real Chromium/Firefox/WebKit source journey tests passed, including exports, accessibility, failure recovery and the received-witness review.

A real Windows archive was built, inspected, extracted into a new temporary folder and launched from an unrelated working directory. The final harness checked nominal/fault CLI exports, refusal to overwrite existing output, a short-window reset, exact package/version/instance identity, actual compiled assets, received recovery witnesses and a real Chromium UI JSON download equal to the frozen API response. Its SHA-256 was `8916633e95f6ae6dc207b82b593e0ddb5638aea88ee8a969c55a6e648662d519`. This development archive honestly records `source_dirty: true`; it is local acceptance evidence, not a publishable clean-source release.

## Reproduce

Use the locked development graph, native compiler and Node 24. Run `python tools/build_native.py`, `python -m pytest --cov=flightlab --cov-report=term-missing`, `python tools/validate_evidence.py`, `npm test`, `npm run build`, `npm run test:e2e`, and `python tools/package_app.py`. The package command installs no software or service: it builds a portable archive and accepts only the actual extracted executable. Its browser development gate needs the locked Playwright Chromium installation.

## Limits and publication boundary

Local native acceptance was Windows only. Linux/macOS archive modes, relative links, ABI and actual executable/UI behavior remain mandatory native CI gates on those operating systems; a Windows synthetic tar test cannot substitute for them. These are unsigned portable folders, not installers or proof of a clean-machine installation. Builds remain educational software-only simulations without flight hardware or control interfaces.

Release decisions use active guards rather than Python assertions. Existing drafts/tags/public releases, ambiguous pushes, interrupted checks and asset collisions fail closed. The coordinator must independently verify the exact-source push checks, all three native release jobs and the exact six public assets/checksum digests before publishing. No push, dispatch, tag or release mutation was performed by this local validation work.
