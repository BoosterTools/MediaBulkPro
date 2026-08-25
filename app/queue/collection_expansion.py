"""Expands a channel/playlist/profile URL into its individual video links.

This is the "extract shorts/video links from a channel" feature: given a
YouTube channel, Instagram profile, or TikTok profile URL, resolve every
video it currently lists — via the backend's flat (metadata-only) extraction
— without downloading anything. The caller decides which of the results to
actually queue.
"""

from __future__ import annotations

from app.downloader.backend import DownloadBackend
from app.downloader.models import CollectionEntry
from app.platforms.detector import detect
from app.platforms.models import UrlMatch


class NotACollectionError(ValueError):
    pass


def expand_collection(url: str, backend: DownloadBackend) -> tuple[UrlMatch, list[CollectionEntry]]:
    """Return the URL's classification plus every video entry found within it.

    Raises :class:`NotACollectionError` if *url* is a single video, not a
    channel/playlist/profile — callers should check ``match.is_collection``
    first if they want to avoid the exception path.
    """
    match = detect(url)
    if not match.is_collection:
        raise NotACollectionError(f"{url} is not a channel, playlist, or profile URL.")
    entries = backend.extract_collection(url)
    return match, entries
