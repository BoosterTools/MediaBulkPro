# Security Policy

## Reporting a vulnerability
Open a private security advisory on GitHub (Security → Advisories → New) rather than a public issue.

## Design commitments
- No hard-coded credentials; optional browser-cookie auth is read locally via yt-dlp and never transmitted anywhere but the target platform.
- Diagnostic reports redact any setting whose key suggests a credential (cookie/token/password/secret/auth).
- FFmpeg and other subprocess calls always use argument lists, never shell string interpolation.
- Output filenames are sanitized against path traversal and Windows-reserved names.
- MediaBulk Pro never executes downloaded files and never bypasses DRM, private-account restrictions, paywalls, or CAPTCHAs.
