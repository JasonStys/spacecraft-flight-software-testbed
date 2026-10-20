# Security and privacy boundaries

By Jason Stys. This is a local educational application, not a public service or operational flight system.

## Threat model

Untrusted query parameters, hostile browser origins, malformed native output, accidental checkpoint corruption and source/build supply-chain mistakes are in scope. Controls: finite primitive allowlists on both sides of the process boundary, full-token native parsing, same-origin/Host guards, CSP, no shell, strict schema/size/count validation, fixed export names, escaped HTML, no dynamic HTML from evidence, path/symlink confinement, pinned lockfiles/action SHAs and CodeQL/dependency audits.

The service binds only127.0.0.1; it cannot be configured for LAN/public access. It rejects duplicate/wrong Host values, foreign Origin and Sec-Fetch-Site cross-site. Static routes cannot expose source, .git, arbitrary downloads or hidden/escaped paths. Headers deny framing, content sniffing, cross-origin embedding through frame policy and unnecessary camera/microphone/location permissions. No remote assets, advertisements, popups, analytics, remote model calls, auto-updater, executable uploads or account credentials exist. Source links open only through an explicit user action with noreferrer.

The API intentionally has no mutation routes or external fetches. CLI history paths are local explicit arguments. SQL values use placeholders; immutable triggers prevent accidental update/delete, and a content hash detects accidental report modification. These are **not** encryption, signatures or access control against local privileged users. Keep runtime/history files outside Git; ignored patterns exclude SQLite, .env, keys, builds and dependencies.

The standard-library HTTP server is not hardened for Internet exposure, hostile multiuser environments or resource-exhaustion attacks. Loopback is not an isolation boundary from malware or other same-user processes. The fixed-worker stdout check is not a sandbox. CRC is forgeable; hashes are not signatures. No real spacecraft secrets or personal data should be supplied; there is no importer for them.

## Supply chain and release

Python runtime is stdlib-only; TypeScript compiles to self-contained local assets. Development dependencies use version/hash locks, actions use commit SHAs, checkout does not persist credentials, and PR jobs cannot publish releases. Release requires passing Validation and CodeQL at the exact source SHA, creates a draft, then packages/smoke-tests all OS builds. SHA256 manifests detect mismatched downloads, but unsigned manifests/binaries do not establish independent publisher authenticity. No request to bypass operating-system trust checks is appropriate.

No toolchain/OS installations, certificate settings, security settings or Docker repairs are performed by the app. Users choose to install developer tools from their official sources; prebuilt app extraction requires no elevation.

## Reporting

Use GitHub private vulnerability reporting if enabled; otherwise contact [Jason Stys](https://github.com/JasonStys) to arrange a private channel before disclosing sensitive details. Do not include exploit payloads against third-party systems, credentials, private telemetry or personal data in public issues. Stop using a release with a suspected integrity problem, preserve local synthetic evidence, and rebuild a reviewed earlier source version or wait for a repaired release.

No certification, military approval, real-time guarantee, flight qualification, safety assurance or absence-of-vulnerabilities guarantee is made.
