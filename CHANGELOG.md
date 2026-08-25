# Changelog

## [0.1.0] - 2026-08-25

### Added
- Project architecture, PySide6 shell, header/sidebar navigation, light/dark/system theming
- SQLite-backed settings, queue, and history with versioned migrations
- Unified URL parser / platform detector: YouTube (video/Shorts/playlist/channel),
  Instagram (Reel/post/profile), TikTok (video/profile/short-link)
- **Channel/profile link extraction** — resolves every video in a YouTube channel,
  Instagram profile, or TikTok profile without downloading anything, with a picker
  dialog to choose which to queue
- Download engine abstraction: real yt-dlp-backed implementation + a deterministic
  mock backend used for all automated tests
- Queue manager: concurrency-limited scheduling, pause/resume/cancel, retry,
  drag-to-reorder, duplicate detection, in-memory output-path collision avoidance
- Bulk URL input with paste/drag-and-drop/.txt/.csv import, auto-dedup, auto-classify
- Queue table with right-click context menu (start/pause/retry/cancel/open/copy/remove)
- Filename templating (`%(title)s` style) with Windows-safe sanitization
- Download History with search/filter/sort/CSV export
- Settings: General, Downloads, Video, File Naming, Advanced (FFmpeg detection, reset)
- Clipboard monitoring (opt-in, never auto-downloads unless explicitly enabled)
- Crash recovery: interrupted downloads detected and offered for resume on next launch
- About/Diagnostics: versions, update check, redacted diagnostic report export
- 67 automated tests covering platform detection, filenames, database, queue state
  machine (concurrency, pause/resume, cancel, retry, collisions, shutdown), collection
  expansion, and crash recovery — plus a full interactive end-to-end pass against the
  real UI with the mock backend, including the channel-extraction feature
- PyInstaller packaging, Inno Setup installer, GitHub Actions CI + Windows release build

### Fixed during development
- `render_template` no longer treats `/` inside a field value (e.g. a video title)
  as a folder separator — only literal `/` in the template itself creates subfolders
- Two concurrently-downloading items that render to the same filename no longer race
  on the same `.part` file — an in-memory path-reservation system assigns unique names
- `QueueManager.shutdown()` now actually blocks until active downloads have paused,
  instead of just requesting a flag and returning immediately
- **Double-dispatch race in the scheduler**: `_try_dispatch()` selected work purely by
  querying `status='queued'` from the database, but a newly-spawned thread doesn't
  update that status until it's actually scheduled by the OS and runs. A second
  `_try_dispatch()` call landing in that window (exactly what `retry_all_failed()`'s
  loop does — one `retry()` call per failed item, each triggering a dispatch pass)
  could pick up the *same* item twice and run it on two racing threads, corrupting
  its output file. Found via a 60-iteration stress test after a flaky test failure;
  fixed by excluding any item already tracked in the active-thread set from dispatch
  selection, and locked in with a dedicated regression test
  (`test_no_double_dispatch_of_same_item`)
