"""Deterministic, network-free backend used by the automated test suite.

Simulates a small file "download" by writing bytes to disk in chunks and
calling the progress hook, so pause/cancel/resume and progress reporting can
all be exercised without touching the network — exactly as the spec's
testing requirements call for.
"""

from __future__ import annotations

from pathlib import Path

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


class MockBackend(DownloadBackend):
    def __init__(
        self, chunk_size: int = 1024, total_size: int = 4096,
        fail_urls: set[str] | None = None, collections: dict[str, list[CollectionEntry]] | None = None,
        force_title: str | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.total_size = total_size
        self.fail_urls = fail_urls or set()
        self.collections = collections or {}
        self.force_title = force_title
        self.extract_calls: list[str] = []
        self.download_calls: list[str] = []

    def extract_info(self, url: str) -> MediaInfo:
        self.extract_calls.append(url)
        if url in self.fail_urls:
            raise RuntimeError("Unable to retrieve media: simulated extraction failure")
        title = self.force_title or f"Mock video {abs(hash(url)) % 10000}"
        return MediaInfo(url=url, video_id=f"id_{abs(hash(url)) % 100000}",
                         title=title, uploader="mock_uploader",
                         duration_secs=42, filesize_approx=self.total_size)

    def extract_collection(self, url: str) -> list[CollectionEntry]:
        return self.collections.get(url, [])

    def download(
        self, request: DownloadRequest, on_progress: ProgressHook, control: ControlToken,
    ) -> DownloadResult:
        self.download_calls.append(request.url)
        if request.url in self.fail_urls:
            return DownloadResult(status=DownloadStatus.FAILED, error_message="simulated failure")

        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        final_path = out_dir / f"{request.filename_template}.{request.output_format}"
        part_path = final_path.with_suffix(final_path.suffix + ".part")

        written = part_path.stat().st_size if part_path.exists() else 0
        mode = "ab" if written else "wb"
        try:
            with open(part_path, mode) as fh:
                while written < self.total_size:
                    control.check()
                    chunk = min(self.chunk_size, self.total_size - written)
                    fh.write(b"0" * chunk)
                    written += chunk
                    on_progress(DownloadProgress(
                        downloaded_bytes=written, total_bytes=self.total_size,
                        speed_bps=self.chunk_size * 10, eta_secs=max(0, (self.total_size - written) // 1),
                    ))
        except DownloadPaused:
            return DownloadResult(status=DownloadStatus.PAUSED)
        except DownloadCancelled:
            part_path.unlink(missing_ok=True)
            return DownloadResult(status=DownloadStatus.CANCELLED)

        part_path.rename(final_path)
        return DownloadResult(status=DownloadStatus.COMPLETED, output_path=str(final_path),
                              file_size=self.total_size)
