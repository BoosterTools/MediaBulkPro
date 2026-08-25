"""Composition root: wires paths, logging, database, repositories, and the
queue manager together."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import AppPaths
from app.core.logging_config import get_logger, setup_logging
from app.database.db import Database
from app.database.repositories import HistoryRepository, QueueRepository, SettingsRepository
from app.downloader.backend import DownloadBackend
from app.downloader.ytdlp_backend import YtDlpBackend
from app.queue.manager import QueueManager


@dataclass
class AppContext:
    paths: AppPaths
    db: Database
    settings: SettingsRepository = field(init=False)
    queue_repo: QueueRepository = field(init=False)
    history: HistoryRepository = field(init=False)
    backend: DownloadBackend = field(init=False)
    queue_manager: QueueManager = field(init=False)

    def __post_init__(self) -> None:
        self.settings = SettingsRepository(self.db)
        self.queue_repo = QueueRepository(self.db)
        self.history = HistoryRepository(self.db)
        self.backend = YtDlpBackend(
            cookies_from_browser=None
        )
        folder = self.settings.get("download_folder") or str(self.paths.downloads_dir)
        self.queue_manager = QueueManager(
            queue_repo=self.queue_repo, history_repo=self.history, backend=self.backend,
            download_folder=folder, filename_template=self.settings.get("filename_template"),
            max_concurrent=int(self.settings.get("concurrent_downloads")),
            duplicate_behavior=self.settings.get("duplicate_behavior"),
            max_retries=int(self.settings.get("retry_count")),
            folder_structure_by_platform=bool(self.settings.get("folder_structure_by_platform")),
        )

    @classmethod
    def create(cls) -> AppContext:
        paths = AppPaths.resolve()
        setup_logging(paths.logs_dir)
        get_logger(__name__).info("Starting MediaBulk Pro; data dir=%s", paths.data_dir)
        return cls(paths=paths, db=Database(paths.database))

    def shutdown(self) -> None:
        self.queue_manager.shutdown()
        self.db.close()
