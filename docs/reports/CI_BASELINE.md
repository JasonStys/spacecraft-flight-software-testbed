# First published CI baseline

Observed 2026-10-20 by Jason Stys. Source commit `16c3140ad3a7b44c4fe648cd11e519193c2fb2c1`.

- [Validation run39504112608](https://github.com/JasonStys/spacecraft-flight-software-testbed/actions/runs/39504112608): **10/10 jobs passed**. Python78tests passed per matrix, browser21tests passed, TypeScript12tests passed, all three OS frozen-app smoke tests passed, native contracts/ASan/UBSan passed, dependency audits passed.
- [GCC coverage job](https://github.com/JasonStys/spacecraft-flight-software-testbed/actions/runs/39504112608/job/118908605592): native executed lines205/205 (100%), functions20/20 (100%), branches365/499 (73.1%). Branch coverage is reported honestly and is not100%; the configured gate is >=90% **line** coverage. Compiler-generated exception/library branches contribute to this result.
- [CodeQL run39504112523](https://github.com/JasonStys/spacecraft-flight-software-testbed/actions/runs/39504112523): **3/3 language jobs passed**. One informational `cpp/complex-condition` readability note was reported in the native configuration validator. It was not a security vulnerability; nevertheless the compound condition was replaced with small independent finite-choice checks. The checks are repeated on the final source revision before release; the note must close through analysis, not manual dismissal.
- Seven integer default replays matched across Linux Python3.12/3.14, Windows3.14 and macOS3.14. The independently tested event deadlines/counts remain the correctness oracle; hashes supplement those tests.
- No Actions artifacts or caches were created by this repo. Nothing elsewhere in the account was deleted. Logs remain available through the linked jobs.

This report is deliberately tied to a real baseline commit. Subsequent final checks and exact release-source SHA are available in the latest workflow runs and release notes; no self-referential report hash or fabricated future run ID is used. A passing workflow does not establish flight qualification, hard real-time correctness, physical accuracy or comprehensive security.
