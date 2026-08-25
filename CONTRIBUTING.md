# Contributing to MediaBulk Pro

## Workflow
1. Branch from `develop`: `feature/<name>` or `bugfix/<name>`.
2. Conventional commit prefixes: `feat:`, `fix:`, `ui:`, `perf:`, `docs:`, `test:`.
3. Run `ruff check .` and `pytest` before pushing. Tests must never depend on live network access to YouTube/Instagram/TikTok — extend `app/downloader/mock_backend.py` instead.
4. Open a PR into `develop`. CI must pass.

## Rules
- `app/` has zero Qt imports. UI-only code lives in `ui/`.
- Never block the GUI thread — long work goes through `ui/widgets/task_thread.py` or the queue manager's background threads.
- One unified download backend abstraction — do not add platform-specific downloader code outside `app/downloader/`.
- Never bypass DRM, private-account restrictions, paywalls, or CAPTCHAs.
- Never hard-code credentials; never upload user URLs, cookies, or history anywhere.
