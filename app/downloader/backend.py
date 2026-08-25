"""Abstract download backend interface.

Every platform (YouTube/Instagram/TikTok) goes through the same interface —
there is exactly one implementation of the extraction/download logic, not
one per platform, per the spec's "unified downloader abstraction" requirement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from app.downloader.models import (
    CollectionEntry,
    ControlToken,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    MediaInfo,
)

ProgressHook = Callable[[DownloadProgress], None]


class DownloadBackend(ABC):
    @abstractmethod
    def extract_info(self, url: str) -> MediaInfo:
        """Resolve metadata for a single video/reel/short without downloading it."""

    @abstractmethod
    def extract_collection(self, url: str) -> list[CollectionEntry]:
        """Expand a channel/playlist/profile URL into its individual video URLs."""

    @abstractmethod
    def download(
        self, request: DownloadRequest, on_progress: ProgressHook, control: ControlToken,
    ) -> DownloadResult:
        """Download one item, calling on_progress periodically. Honors control's
        pause/cancel flags cooperatively."""
