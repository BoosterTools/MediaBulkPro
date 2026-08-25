<p align="center">
  <img src="assets/icons/mediabulk.png" width="96" alt="MediaBulk Pro logo">
</p>

<h1 align="center">MediaBulk Pro</h1>
<p align="center"><b>Professional Bulk Video Downloader</b></p>

MediaBulk Pro is a Windows desktop app for organized bulk downloading of publicly accessible media from YouTube, YouTube Shorts, Instagram Reels, and TikTok, built on [yt-dlp](https://github.com/yt-dlp/yt-dlp).

It only downloads content you're authorized to access. It never bypasses DRM, private-account restrictions, paywalls, or CAPTCHAs, and never uploads your URLs, cookies, or history anywhere.

## Features

- **Bulk URL input** — paste hundreds of URLs, drag-and-drop `.txt`/`.csv`, automatic de-dup and platform detection
- **Channel/profile link extraction** — paste a YouTube channel, Instagram profile, or TikTok profile URL and MediaBulk Pro resolves every video/short/reel it currently lists, so you can pick which ones to queue
- **Concurrent downloads** with a configurable limit, per-item progress/speed/ETA, pause/resume/cancel/retry
- **Quality & format selection** — up to 4K, audio-only, MP4/MKV/WebM/MP3/M4A/WAV/Opus
- **Smart filename templates** (`%(uploader)s - %(title)s`, etc.) with automatic Windows-safe sanitization and collision avoidance
- **Duplicate detection** against download history — skip or re-download, your choice
- **Crash recovery** — an unclean shutdown is detected on next launch with a resume prompt
- **Download history** with search/filter/sort/export
- **Optional clipboard monitoring** — never auto-downloads unless you explicitly enable it
- **Diagnostics** — versions, update check, exportable report with secrets redacted

## Installation

Download `MediaBulkPro-Setup.exe` from the [Releases](../../releases) page and run it. No Python required. **FFmpeg must be installed separately** and available on your `PATH` — MediaBulk Pro detects it automatically and will tell you in Settings if it's missing (needed for merging separate video+audio streams).

## Development setup

```powershell
git clone https://github.com/<you>/MediaBulkPro.git
cd MediaBulkPro
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

### Run locally

```powershell
python main.py
```

### Run tests

```powershell
pytest
ruff check .
```

All automated tests run against a **mock download backend** (`app/downloader/mock_backend.py`) — none of them touch YouTube, Instagram, or TikTok, per the project's own testing requirements. The real `yt-dlp`-backed engine (`app/downloader/ytdlp_backend.py`) is exercised by actually running the app.

### Build the Windows executable

```powershell
python scripts/make_icon.py
python scripts/build_exe.py
```

Installer via Inno Setup (`scripts/installer.iss`) happens automatically in CI on a version tag.

## GitHub workflow

Branches: `main` · `develop` · `feature/*` · `bugfix/*` · `release/*`
Commit prefixes: `feat:` `fix:` `ui:` `perf:` `docs:` `test:` `chore:`

- **CI** (`.github/workflows/ci.yml`) — ruff, syntax check, pytest on Windows + Ubuntu.
- **Windows Build** (`.github/workflows/build-windows.yml`) — builds the exe + installer, generates SHA-256 checksums, and publishes a GitHub Release on a `v*` tag.

## Project structure

```
mediabulk_pro/
├── app/                    # business logic — no Qt imports
│   ├── core/                # config, logging, app context, diagnostics
│   ├── database/             # SQLite wrapper, migrations, repositories
│   ├── downloader/            # backend abstraction: yt-dlp real impl + mock for tests
│   ├── platforms/               # URL parser / platform+media-type detection
│   ├── queue/                    # concurrency-limited state machine, dedup, crash recovery
│   └── utils/                     # filename sanitization/templating, formatting
├── ui/                      # PySide6 — windows, pages, widgets, dialogs, theme
├── tests/
├── assets/icons/
├── scripts/                 # build_exe.py, installer.iss, make_icon.py
├── .github/workflows/
└── main.py
```

Business logic in `app/` has zero Qt dependency by design — the entire download queue state machine (`app/queue/manager.py`) is plain `threading`, so it's testable without an event loop and reusable outside the GUI.

## Architecture note: the download engine abstraction

There is exactly one downloader abstraction (`app/downloader/backend.py`) used for every platform — YouTube, Instagram, and TikTok all go through the same `extract_info` / `extract_collection` / `download` interface, backed by yt-dlp's own platform extractors. Nothing is duplicated per platform.

Pause/resume is implemented the standard way for yt-dlp-based GUIs: a shared `ControlToken` is checked from inside yt-dlp's `progress_hooks` callback; requesting a pause raises a small exception that unwinds the download, and because `continuedl` is always on, resuming the same URL/output path picks the `.part` file back up automatically.

## Security notes

- No credentials are hard-coded. Optional cookie-based auth (for content you're authorized to access) is read from your browser via yt-dlp's own `cookiesfrombrowser`, never uploaded anywhere.
- Diagnostic reports redact anything with "cookie", "token", "password", "secret", or "auth" in its settings key.
- FFmpeg and yt-dlp subprocess calls use argument lists, never shell strings.
- All output filenames are sanitized against Windows-reserved names/characters and path traversal.

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## A note on platform Terms of Service

Downloading video content in bulk from YouTube, Instagram, and TikTok is against those platforms' Terms of Service in most cases, similar to how `yt-dlp` itself operates in a tolerated gray area for personal/fair-use downloading (your own uploads, Creative Commons content, archival, accessibility). MediaBulk Pro doesn't circumvent any platform's access controls — it only automates what a browser already does for public pages. Use it for content you have the right to download.

## License

MIT — see [LICENSE](LICENSE).
