"""Concurrency-limited queue state machine.

Deliberately free of Qt: uses plain ``threading`` and a small manual
scheduler instead of QThreadPool, so it can be unit tested with a
:class:`~app.downloader.mock_backend.MockBackend` and no event loop at all.
A thin Qt-facing wrapper (``ui/queue_controller.py``) subscribes to
``on_event`` and turns each :class:`QueueEvent` into a Qt signal.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime

from app.database.repositories import HistoryEntry, HistoryRepository, QueueItem, QueueRepository
from app.downloader.backend import DownloadBackend
from app.downloader.models import ControlToken, DownloadProgress, DownloadRequest, DownloadStatus
from app.platforms.detector import detect
from app.queue.dedup import is_already_queued, is_duplicate
from app.queue.models import QueueEvent
from app.utils.filenames import build_context, render_template, sanitize_folder_component

TERMINAL_STATUSES = {"completed", "failed", "cancelled", "skipped_duplicate"}
ACTIVE_STATUSES = {"extracting", "downloading"}


class QueueManager:
    def __init__(
        self,
        queue_repo: QueueRepository,
        history_repo: HistoryRepository,
        backend: DownloadBackend,
        download_folder: str,
        filename_template: str = "%(uploader)s - %(title)s",
        max_concurrent: int = 4,
        duplicate_behavior: str = "skip",
        max_retries: int = 3,
        folder_structure_by_platform: bool = True,
        on_event: Callable[[QueueEvent], None] | None = None,
    ) -> None:
        self.queue = queue_repo
        self.history = history_repo
        self.backend = backend
        self.download_folder = download_folder
        self.filename_template = filename_template
        self.max_concurrent = max_concurrent
        self.duplicate_behavior = duplicate_behavior
        self.max_retries = max_retries
        self.folder_structure_by_platform = folder_structure_by_platform
        self.on_event = on_event or (lambda e: None)

        self._lock = threading.RLock()
        self._active: dict[int, threading.Thread] = {}
        self._tokens: dict[int, ControlToken] = {}
        self._reserved_paths: dict[int, str] = {}  # item_id -> claimed output path (no extension)
        self._stopped = False

    # -- adding work ------------------------------------------------------
    def enqueue_url(self, url: str, quality: str = "best", output_format: str = "mp4",
                    source_batch: str | None = None) -> int | None:
        match = detect(url)
        if match.video_id and is_already_queued(match.video_id, self.queue):
            return None  # already queued or actively processing; avoid a duplicate row
        item = QueueItem(
            id=None, url=url, platform=match.platform.value, media_type=match.media_type.value,
            video_id=match.video_id, quality=quality, output_format=output_format,
            source_batch=source_batch,
        )
        item_id = self.queue.add(item)
        self.on_event(QueueEvent("added", item_id, {"url": url}))
        self._try_dispatch()
        return item_id

    def enqueue_many(self, urls: list[str], **kwargs) -> list[int]:
        return [i for u in urls if (i := self.enqueue_url(u, **kwargs)) is not None]

    # -- controls -----------------------------------------------------------
    def pause(self, item_id: int) -> None:
        with self._lock:
            token = self._tokens.get(item_id)
            if token is not None:
                token.request_pause()
            else:
                item = self.queue.get(item_id)
                if item and item.status == "queued":
                    self._set_status(item_id, "paused")

    def resume(self, item_id: int) -> None:
        item = self.queue.get(item_id)
        if item and item.status == "paused":
            self._set_status(item_id, "queued")
            self._try_dispatch()

    def cancel(self, item_id: int) -> None:
        with self._lock:
            token = self._tokens.get(item_id)
        if token is not None:
            token.request_cancel()
        else:
            self._set_status(item_id, "cancelled")

    def retry(self, item_id: int) -> None:
        item = self.queue.get(item_id)
        if item and item.status == "failed":
            self.queue.update(item_id, status="queued", error_message=None,
                              retry_count=item.retry_count + 1, progress=0)
            self.on_event(QueueEvent("status_changed", item_id, {"status": "queued"}))
            self._try_dispatch()

    def retry_all_failed(self) -> int:
        ids = self.queue.ids_by_status("failed")
        for item_id in ids:
            self.retry(item_id)
        return len(ids)

    def remove(self, item_id: int) -> None:
        with self._lock:
            if item_id in self._active:
                return  # can't remove an actively-running item; cancel first
        self.queue.remove(item_id)
        self.on_event(QueueEvent("removed", item_id, {}))

    def reorder(self, ordered_ids: list[int]) -> None:
        self.queue.reorder(ordered_ids)
        self.on_event(QueueEvent("reordered", 0, {"order": ordered_ids}))

    def set_concurrency(self, n: int) -> None:
        with self._lock:
            self.max_concurrent = max(1, n)
        self._try_dispatch()

    def shutdown(self, timeout: float = 5.0) -> None:
        """Stop accepting new dispatches and block until active downloads
        have actually paused, so no background thread can touch the
        database after the caller closes it (e.g. on app exit). Pausing
        rather than cancelling preserves the .part file so the download can
        resume on next launch instead of losing progress."""
        with self._lock:
            self._stopped = True
            for token in self._tokens.values():
                token.request_pause()
            threads = list(self._active.values())
        for thread in threads:
            thread.join(timeout=timeout)

    def wait_idle(self, timeout: float = 10.0) -> bool:
        """Test helper: block until no items are queued/active, or timeout."""
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                active = bool(self._active)
            pending = bool(self.queue.ids_by_status("queued"))
            if not active and not pending:
                return True
            time.sleep(0.01)
        return False

    # -- output path collision avoidance -------------------------------------
    def _reserve_output_path(self, item_id: int, folder: str, stem: str, ext: str) -> str:
        """Claim a unique '<folder>/<stem>[ (n)]' among files already on disk
        AND paths other currently-active items have already claimed, so two
        concurrently-downloading items can never collide on the same .part
        file even before either one exists yet."""
        from pathlib import Path
        with self._lock:
            candidate = stem
            n = 1
            while True:
                full = str(Path(folder) / f"{candidate}.{ext}")
                taken = Path(full).exists() or any(
                    p == full for other_id, p in self._reserved_paths.items() if other_id != item_id
                )
                if not taken:
                    self._reserved_paths[item_id] = full
                    return candidate
                candidate = f"{stem} ({n})"
                n += 1

    def _release_output_path(self, item_id: int) -> None:
        with self._lock:
            self._reserved_paths.pop(item_id, None)

    # -- internal scheduler -------------------------------------------------
    def _set_status(self, item_id: int, status: str, **extra) -> None:
        self.queue.update(item_id, status=status, **extra)
        self.on_event(QueueEvent("status_changed", item_id, {"status": status, **extra}))

    def _try_dispatch(self) -> None:
        with self._lock:
            if self._stopped:
                return
            available = self.max_concurrent - len(self._active)
            if available <= 0:
                return
            # A newly-spawned thread doesn't update the DB status away from
            # 'queued' until it actually gets scheduled and runs — so a
            # second _try_dispatch() call arriving before that happens (e.g.
            # from retry_all_failed()'s loop calling retry() repeatedly)
            # must not be allowed to dispatch the same item_id a second
            # time. self._active is updated atomically within this same
            # locked section, so checking against it here closes the race.
            pending_ids = [
                i for i in self.queue.ids_by_status("queued") if i not in self._active
            ][:available]
            for item_id in pending_ids:
                token = ControlToken()
                self._tokens[item_id] = token
                thread = threading.Thread(target=self._run_item, args=(item_id, token), daemon=True)
                self._active[item_id] = thread
                thread.start()

    def _run_item(self, item_id: int, token: ControlToken) -> None:
        try:
            self._process_item(item_id, token)
        finally:
            with self._lock:
                self._active.pop(item_id, None)
                self._tokens.pop(item_id, None)
            self._try_dispatch()

    def _process_item(self, item_id: int, token: ControlToken) -> None:
        item = self.queue.get(item_id)
        if item is None:
            return

        self._set_status(item_id, "extracting")
        try:
            info = self.backend.extract_info(item.url)
        except Exception as exc:  # noqa: BLE001
            self._set_status(item_id, "failed", error_message=str(exc))
            return

        self.queue.update(
            item_id, title=info.title, uploader=info.uploader, video_id=info.video_id,
            duration_secs=info.duration_secs, thumbnail_url=info.thumbnail_url,
        )

        if self.duplicate_behavior == "skip" and is_duplicate(info.video_id, item.url, self.history):
            self._set_status(item_id, "skipped_duplicate")
            return

        self._set_status(item_id, "downloading")

        folder = self.download_folder
        if self.folder_structure_by_platform:
            folder = f"{folder}/{sanitize_folder_component(item.platform.title())}"
        context = build_context(info.title, info.uploader, item.platform, info.upload_date,
                                info.video_id or "", item.output_format)
        filename = render_template(self.filename_template, context)
        filename = self._reserve_output_path(item_id, folder, filename, item.output_format)

        request = DownloadRequest(
            url=item.url, output_dir=folder, filename_template=filename,
            quality=item.quality, output_format=item.output_format,
        )

        def on_progress(p: DownloadProgress) -> None:
            self.queue.update(
                item_id, progress=p.percent, downloaded_bytes=p.downloaded_bytes,
                total_bytes=p.total_bytes, speed_bps=p.speed_bps, eta_secs=p.eta_secs,
            )
            self.on_event(QueueEvent("progress", item_id, {
                "percent": p.percent, "speed_bps": p.speed_bps, "eta_secs": p.eta_secs,
            }))

        result = self.backend.download(request, on_progress, token)

        if result.status != DownloadStatus.PAUSED:
            # A paused item keeps its reservation — its .part file still
            # occupies that exact path until it resumes or is cancelled.
            self._release_output_path(item_id)

        if result.status == DownloadStatus.COMPLETED:
            self._set_status(item_id, "completed", progress=100, output_path=result.output_path)
            self.history.add(HistoryEntry(
                id=None, title=info.title, url=item.url, platform=item.platform,
                video_id=info.video_id, date=datetime.now().isoformat(timespec="seconds"),
                file_path=result.output_path, file_size=result.file_size,
                quality=item.quality, status="completed",
            ))
        elif result.status == DownloadStatus.PAUSED:
            self._set_status(item_id, "paused")
        elif result.status == DownloadStatus.CANCELLED:
            self._set_status(item_id, "cancelled")
        else:
            self._set_status(item_id, "failed", error_message=result.error_message)
            self.history.add(HistoryEntry(
                id=None, title=info.title, url=item.url, platform=item.platform,
                video_id=info.video_id, date=datetime.now().isoformat(timespec="seconds"),
                file_path=None, file_size=None, quality=item.quality, status="failed",
            ))
