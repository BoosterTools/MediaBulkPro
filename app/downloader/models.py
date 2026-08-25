"""Backend-agnostic data types for the download engine abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED_DUPLICATE = "skipped_duplicate"


@dataclass
class MediaInfo:
    """Metadata for one piece of media, resolved without downloading it."""
    url: str
    video_id: str | None
    title: str
    uploader: str = ""
    duration_secs: int | None = None
    thumbnail_url: str | None = None
    upload_date: datetime | None = None
    filesize_approx: int | None = None
    available_qualities: list[str] = field(default_factory=list)


@dataclass
class CollectionEntry:
    """One item found while expanding a channel/playlist/profile URL."""
    url: str
    title: str = ""
    video_id: str | None = None
    duration_secs: int | None = None
    thumbnail_url: str | None = None


@dataclass
class DownloadProgress:
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed_bps: float | None = None
    eta_secs: int | None = None

    @property
    def percent(self) -> float:
        if not self.total_bytes:
            return 0.0
        return min(100.0, (self.downloaded_bytes / self.total_bytes) * 100)


@dataclass
class DownloadRequest:
    url: str
    output_dir: str
    filename_template: str
    quality: str = "best"
    output_format: str = "mp4"
    audio_only: bool = False


@dataclass
class DownloadResult:
    status: DownloadStatus
    output_path: str | None = None
    error_message: str | None = None
    file_size: int | None = None


class DownloadPaused(Exception):
    """Raised from inside a progress hook to cooperatively stop a download for pause."""


class DownloadCancelled(Exception):
    """Raised from inside a progress hook to cooperatively stop a download for cancel."""


class ControlToken:
    """Shared, thread-safe flag checked by the backend during a download."""

    def __init__(self) -> None:
        self._paused = False
        self._cancelled = False

    def request_pause(self) -> None:
        self._paused = True

    def request_cancel(self) -> None:
        self._cancelled = True

    def reset_pause(self) -> None:
        self._paused = False

    def check(self) -> None:
        """Call from inside a progress hook; raises to interrupt the download."""
        if self._cancelled:
            raise DownloadCancelled()
        if self._paused:
            raise DownloadPaused()

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def paused(self) -> bool:
        return self._paused
