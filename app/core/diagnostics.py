"""Version info and diagnostic report generation.

The exported report explicitly excludes anything resembling credentials,
cookies, or tokens — only versions, settings (values only, not secrets),
and environment facts.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from app.core.config import APP_NAME, APP_VERSION, ffmpeg_available

_SENSITIVE_KEY_HINTS = ("cookie", "token", "password", "secret", "auth", "key")


def yt_dlp_version() -> str:
    try:
        import yt_dlp
        return getattr(yt_dlp.version, "__version__", "unknown")
    except Exception:  # noqa: BLE001
        return "not installed"


def ffmpeg_version() -> str:
    if not ffmpeg_available():
        return "not found"
    try:
        result = subprocess.run(  # noqa: S603,S607
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        first_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return first_line
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def check_for_updates() -> dict[str, str]:
    """Best-effort check of the latest published yt-dlp version on PyPI.

    Requires network access; callers should run this off the GUI thread and
    handle failures gracefully (offline is a normal condition, not an error).
    """
    import requests
    resp = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=8)
    resp.raise_for_status()
    latest = resp.json()["info"]["version"]
    current = yt_dlp_version()
    return {"current": current, "latest": latest, "update_available": str(latest != current)}


def _redact(settings: dict) -> dict:
    return {
        k: ("<redacted>" if any(h in k.lower() for h in _SENSITIVE_KEY_HINTS) else v)
        for k, v in settings.items()
    }


def build_diagnostic_report(settings: dict, paths_summary: dict[str, str]) -> str:
    lines = [
        f"{APP_NAME} Diagnostic Report",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "-- Versions --",
        f"{APP_NAME}: {APP_VERSION}",
        f"Python: {sys.version.split()[0]}",
        f"Platform: {platform.platform()}",
        f"yt-dlp: {yt_dlp_version()}",
        f"FFmpeg: {ffmpeg_version()}",
        "",
        "-- Paths --",
        *[f"{k}: {v}" for k, v in paths_summary.items()],
        "",
        "-- Settings (sensitive values redacted) --",
        *[f"{k}: {v}" for k, v in _redact(settings).items()],
    ]
    return "\n".join(lines)


def write_diagnostic_report(target_dir: Path, settings: dict, paths_summary: dict[str, str]) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"diagnostic-report-{datetime.now():%Y%m%d-%H%M%S}.txt"
    path.write_text(build_diagnostic_report(settings, paths_summary), encoding="utf-8")
    return path
