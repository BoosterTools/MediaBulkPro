"""Real download backend, built on yt-dlp.

This is the only place yt-dlp is imported. Pause/cancel are implemented the
standard community way for yt-dlp GUI wrappers: ``control.check()`` is called
from inside yt-dlp's ``progress_hooks`` callback on every progress tick, and
raises a small exception that unwinds yt-dlp's download loop. Because we
never disable yt-dlp's default ``--continue`` behaviour, resuming the same
URL/output path afterwards picks the ``.part`` file back up automatically.

Requires network access to the source platform, so it cannot be exercised
by the automated test suite; :mod:`app.downloader.mock_backend` stands in
for tests instead.
"""

from __future__ import annotations

from datetime import datetime

from app.core.logging_config import get_logger
from app.downloader.backend import DownloadBackend, ProgressHook
from app.downloader.models import (
    CollectionEntry,
    ControlToken,
    DownloadCancelled,
    DownloadPaused,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    MediaInfo,
)
from app.utils.filenames import render_template

log = get_logger(__name__)

_QUALITY_FORMAT_MAP = {
    "best": "bestvideo+bestaudio/best",
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "audio_only": "bestaudio/best",
}


def _base_opts() -> dict:
    return {
        "quiet": True, "no_warnings": True, "noprogress": False,
        "ignoreerrors": False, "continuedl": True, "noplaylist": True,
        "retries": 3,
    }


class YtDlpBackend(DownloadBackend):
    def __init__(self, cookies_from_browser: str | None = None) -> None:
        self._cookies_from_browser = cookies_from_browser

    def _with_cookies(self, opts: dict) -> dict:
        if self._cookies_from_browser:
            opts["cookiesfrombrowser"] = (self._cookies_from_browser,)
        return opts

    def extract_info(self, url: str) -> MediaInfo:
        import yt_dlp

        opts = self._with_cookies({**_base_opts(), "skip_download": True})
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        upload_date = None
        if info.get("upload_date"):
            try:
                upload_date = datetime.strptime(info["upload_date"], "%Y%m%d")
            except ValueError:
                upload_date = None
        return MediaInfo(
            url=url, video_id=info.get("id"), title=info.get("title") or "Untitled",
            uploader=info.get("uploader") or info.get("channel") or "",
            duration_secs=info.get("duration"), thumbnail_url=info.get("thumbnail"),
            upload_date=upload_date, filesize_approx=info.get("filesize_approx"),
            available_qualities=sorted({
                f"{f.get('height')}p" for f in info.get("formats", []) if f.get("height")
            }, key=lambda s: int(s.rstrip("p")), reverse=True),
        )

    def extract_collection(self, url: str) -> list[CollectionEntry]:
        import yt_dlp

        opts = self._with_cookies({
            **_base_opts(), "extract_flat": "in_playlist", "skip_download": True,
            "noplaylist": False,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        entries = info.get("entries") or []
        results: list[CollectionEntry] = []
        for e in entries:
            if not e:
                continue
            entry_url = e.get("url") or e.get("webpage_url") or ""
            if not entry_url:
                continue
            results.append(CollectionEntry(
                url=entry_url, title=e.get("title") or "", video_id=e.get("id"),
                duration_secs=e.get("duration"), thumbnail_url=e.get("thumbnail"),
            ))
        return results

    def download(
        self, request: DownloadRequest, on_progress: ProgressHook, control: ControlToken,
    ) -> DownloadResult:
        import yt_dlp

        def hook(d: dict) -> None:
            control.check()
            if d.get("status") == "downloading":
                on_progress(DownloadProgress(
                    downloaded_bytes=d.get("downloaded_bytes") or 0,
                    total_bytes=d.get("total_bytes") or d.get("total_bytes_estimate"),
                    speed_bps=d.get("speed"), eta_secs=d.get("eta"),
                ))

        fmt = _QUALITY_FORMAT_MAP.get(request.quality, _QUALITY_FORMAT_MAP["best"])
        outtmpl = f"{request.output_dir}/{request.filename_template}.%(ext)s"
        opts = self._with_cookies({
            **_base_opts(),
            "format": fmt if not request.audio_only else _QUALITY_FORMAT_MAP["audio_only"],
            "outtmpl": outtmpl,
            "progress_hooks": [hook],
            "merge_output_format": request.output_format,
        })
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(request.url, download=True)
            path = ydl.prepare_filename(info)
            return DownloadResult(status=DownloadStatus.COMPLETED, output_path=path,
                                  file_size=info.get("filesize_approx"))
        except DownloadPaused:
            return DownloadResult(status=DownloadStatus.PAUSED)
        except DownloadCancelled:
            return DownloadResult(status=DownloadStatus.CANCELLED)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI as a failure, not swallowed
            log.error("Download failed for %s: %s", request.url, exc)
            return DownloadResult(status=DownloadStatus.FAILED, error_message=str(exc))


def render_output_template(template: str, context: dict[str, str]) -> str:
    return render_template(template, context)
