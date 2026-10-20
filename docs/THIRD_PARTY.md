# References and license notices

By Jason Stys. Project code is original and MIT licensed. Build/release/HTTP evidence infrastructure is adapted from the author's earlier portfolio work; the executive/codec/scenario/UI implementation is specific to this repo.

## Concept references, not integrated code

- [NASA SmallSat mission design tools](https://www.nasa.gov/smallsat-institute/space-mission-design-tools/) describes generic cFS architecture, lab-app limitations and NOS3's software-only environment. This project is not a NASA flight distribution, uses no cFS APIs and makes no NOS3 compatibility claim.
- [NASA NTRS — The State of NOS3 (2024)](https://ntrs.nasa.gov/citations/20240004699) provides context for software-only digital twin development. This repo is a much smaller teaching model, not a reproduction or substitute for that tool.
- [Python zlib documentation](https://docs.python.org/3/library/zlib.html#zlib.crc32) describes CRC32 as a noncryptographic checksum. The native implementation uses the standard reflected CRC32 check vector; it is not a security authenticator.

## Runtime and distribution

The native core uses the C++ standard library. Python code uses only CPython's standard library. CPython license is included in `licenses/PYTHON.txt`. PyInstaller bootloader is distributed under its GPL licensing exception permitting bundled applications; the installed locked distribution's full COPYING notice is copied into each bundle. See [PyInstaller license](https://pyinstaller.org/en/stable/license.html). Project MIT license is included too. Microsoft static C++ runtime components follow Microsoft's redistribution license; Linux/macOS depend on the OS-supported runtime/ABI. This is not an assurance of universal OS compatibility.

## Development packages

Exact package versions/integrities are in package-lock.json and requirements-dev.lock. TypeScript (Apache-2.0), Vite/Vitest/Prettier (MIT), Playwright and axe-core (Apache-2.0/MPL-2.0 respectively), pytest/Hypothesis/ruff/mypy/coverage (their distributed licenses) are development/build/test tools, not browser runtime libraries. npm/locked distributions retain their license metadata. No third-party photos, icons, fonts, real flight telemetry, model weights or datasets are included. The spacecraft illustration is authored SVG in the HTML. Dependency audits are a time-specific check, not a guarantee about future advisories.
