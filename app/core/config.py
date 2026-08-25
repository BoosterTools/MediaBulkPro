"""Application-wide constants and per-user directory resolution."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "MediaBulk Pro"
APP_SUBTITLE = "Professional Bulk Video Downloader"
ORG_NAME = "MediaBulkPro"
DB_FILENAME = "mediabulk.db"
APP_VERSION = "0.1.0"


def _user_data_root() -> Path:
    override = os.environ.get("MEDIABULK_DATA_DIR")
    if override:
        return Path(override)
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "MediaBulkPro"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "mediabulkpro"


@dataclass(frozen=True)
class AppPaths:
    data_dir: Path
    logs_dir: Path
    cache_dir: Path
    downloads_dir: Path
    database: Path

    @classmethod
    def resolve(cls) -> AppPaths:
        root = _user_data_root()
        downloads_override = os.environ.get("MEDIABULK_DOWNLOADS_DIR")
        downloads = Path(downloads_override) if downloads_override else default_downloads_folder()
        paths = cls(
            data_dir=root, logs_dir=root / "logs", cache_dir=root / "cache",
            downloads_dir=downloads, database=root / DB_FILENAME,
        )
        for d in (paths.data_dir, paths.logs_dir, paths.cache_dir, paths.downloads_dir):
            d.mkdir(parents=True, exist_ok=True)
        return paths


def default_downloads_folder() -> Path:
    return Path.home() / "Downloads" / "MediaBulkPro"


def ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None
