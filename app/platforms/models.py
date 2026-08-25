"""Shared data types for platform/URL detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    UNKNOWN = "unknown"


class MediaType(str, Enum):
    VIDEO = "video"
    SHORT = "short"          # YouTube Shorts
    REEL = "reel"             # Instagram Reels
    PLAYLIST = "playlist"     # YouTube playlist
    CHANNEL = "channel"       # YouTube channel / Instagram or TikTok profile
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class UrlMatch:
    url: str
    platform: Platform
    media_type: MediaType
    video_id: str | None = None

    @property
    def is_collection(self) -> bool:
        """True for channels/playlists/profiles that expand into many URLs."""
        return self.media_type in (MediaType.PLAYLIST, MediaType.CHANNEL)

    @property
    def is_supported(self) -> bool:
        return self.platform != Platform.UNKNOWN and self.media_type != MediaType.UNKNOWN
