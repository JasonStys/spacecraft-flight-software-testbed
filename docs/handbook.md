# Spacecraft Flight Software Testbed handbook

By Jason Stys.

The released 1.1.0 portable app brings the recovery-observability review into a source-bound downloadable bundle: compare onboard transitions with received confirmation, then export the same evidence shown in the UI.

The original deterministic C++ executive and Python replay oracle remain intact. Versioned archives, native-safe POSIX packaging and an extracted-executable Chromium journey make the new received-witness feature reviewable beyond a source checkout. An independent boot/reset oracle and downloaded JSON comparison prevent a static page or source-service fallback from passing acceptance.

## Read the documentation

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions, and the workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)
- [releases/v1.1.0](releases/v1.1.0.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)

### Security and validation

- [SECURITY](SECURITY.md)
- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`5f9dc95ad5df564373d1304b13e4bb2464d13842`](https://github.com/JasonStys/spacecraft-flight-software-testbed/tree/5f9dc95ad5df564373d1304b13e4bb2464d13842). The observed functional workflow baseline is `5f9dc95ad5df564373d1304b13e4bb2464d13842`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_REFRESH_20261109.md)
- [Current Actions](https://github.com/JasonStys/spacecraft-flight-software-testbed/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Educational software-only executive; no flight hardware, operational SAFE assertion or mission qualification.
- Unsigned portable folder, not an installer or clean-machine installation proof. Exact-source three-OS builds and asset digests require publication review.
- Unsigned desktop portable folders, not system installers or clean-machine proof. Three-OS extracted-native checks drive an owned URL; default OS browser opening remains manual.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
