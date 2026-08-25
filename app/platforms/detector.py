"""Unified URL parser: detects platform and media type from a raw URL string.

Pure regex/string logic with no network calls, so it is fully unit-testable
and instant to run over thousands of pasted URLs.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.platforms.models import MediaType, Platform, UrlMatch

_YT_WATCH = re.compile(r"[?&]v=([\w-]{6,})")
_YT_SHORT_HOST = re.compile(r"^(www\.)?youtu\.be$")
_YT_SHORTS = re.compile(r"/shorts/([\w-]{6,})")
_YT_PLAYLIST = re.compile(r"[?&]list=([\w-]+)")
_YT_CHANNEL = re.compile(r"/(channel/[\w-]+|c/[\w.-]+|user/[\w.-]+|@[\w.-]+)/?$")

_IG_REEL = re.compile(r"/reels?/([\w-]+)/?")
_IG_POST = re.compile(r"/p/([\w-]+)/?")
_IG_PROFILE = re.compile(r"^/([\w.]+)/?$")

_TT_VIDEO = re.compile(r"/@[\w.-]+/video/(\d+)")
_TT_PROFILE = re.compile(r"^/@[\w.-]+/?$")
_TT_SHORT_HOST = re.compile(r"^(vm|vt)\.tiktok\.com$")


def _host(url: str) -> str:
    return (urlparse(url).netloc or "").lower()


def _path(url: str) -> str:
    return urlparse(url).path or "/"


def detect(url: str) -> UrlMatch:
    """Classify a single URL. Unrecognized URLs come back as UNKNOWN, not raise."""
    url = url.strip()
    if not url:
        return UrlMatch(url=url, platform=Platform.UNKNOWN, media_type=MediaType.UNKNOWN)

    host = _host(url)
    path = _path(url)

    if "youtube.com" in host or _YT_SHORT_HOST.match(host):
        return _detect_youtube(url, host, path)
    if "instagram.com" in host:
        return _detect_instagram(url, path)
    if "tiktok.com" in host:
        return _detect_tiktok(url, host, path)

    return UrlMatch(url=url, platform=Platform.UNKNOWN, media_type=MediaType.UNKNOWN)


def _detect_youtube(url: str, host: str, path: str) -> UrlMatch:
    if _YT_SHORT_HOST.match(host):
        vid = path.strip("/").split("/")[0] or None
        return UrlMatch(url, Platform.YOUTUBE, MediaType.VIDEO, vid)

    m = _YT_SHORTS.search(path)
    if m:
        return UrlMatch(url, Platform.YOUTUBE, MediaType.SHORT, m.group(1))

    m = _YT_WATCH.search(url)
    if m:
        # A watch URL can also carry a list= param (video within a playlist);
        # we still treat it as a single video unless there's no video id at all.
        return UrlMatch(url, Platform.YOUTUBE, MediaType.VIDEO, m.group(1))

    m = _YT_PLAYLIST.search(url)
    if m:
        return UrlMatch(url, Platform.YOUTUBE, MediaType.PLAYLIST, m.group(1))

    m = _YT_CHANNEL.search(path)
    if m:
        return UrlMatch(url, Platform.YOUTUBE, MediaType.CHANNEL, m.group(1))

    return UrlMatch(url, Platform.YOUTUBE, MediaType.UNKNOWN)


def _detect_instagram(url: str, path: str) -> UrlMatch:
    m = _IG_REEL.search(path)
    if m:
        return UrlMatch(url, Platform.INSTAGRAM, MediaType.REEL, m.group(1))
    m = _IG_POST.search(path)
    if m:
        return UrlMatch(url, Platform.INSTAGRAM, MediaType.VIDEO, m.group(1))
    m = _IG_PROFILE.match(path)
    if m and m.group(1) not in {"reel", "reels", "p", "tv", "stories", "explore"}:
        return UrlMatch(url, Platform.INSTAGRAM, MediaType.CHANNEL, m.group(1))
    return UrlMatch(url, Platform.INSTAGRAM, MediaType.UNKNOWN)


def _detect_tiktok(url: str, host: str, path: str) -> UrlMatch:
    if _TT_SHORT_HOST.match(host):
        # Short links resolve server-side; we mark them as an unresolved video
        # and let the real extractor follow the redirect at extraction time.
        return UrlMatch(url, Platform.TIKTOK, MediaType.VIDEO, None)
    m = _TT_VIDEO.search(path)
    if m:
        return UrlMatch(url, Platform.TIKTOK, MediaType.VIDEO, m.group(1))
    m = _TT_PROFILE.match(path)
    if m:
        return UrlMatch(url, Platform.TIKTOK, MediaType.CHANNEL, path.strip("/"))
    return UrlMatch(url, Platform.TIKTOK, MediaType.UNKNOWN)


def detect_many(urls: list[str]) -> list[UrlMatch]:
    return [detect(u) for u in urls]


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Order-preserving de-duplication after light normalization (trim, strip trailing slash)."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in urls:
        u = raw.strip()
        if not u:
            continue
        normalized = u.rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(u)
    return result
