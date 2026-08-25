import pytest

from app.database.db import Database


@pytest.fixture
def db(tmp_path):
    db_dir = tmp_path / "_dbstore"
    db_dir.mkdir()
    database = Database(db_dir / "test.db")
    yield database
    database.close()


@pytest.fixture
def make_manager(db, tmp_path):
    """Factory for QueueManager instances used across the queue-manager
    tests. Every manager created through this fixture is automatically
    shut down (joining any active threads) at test teardown — regardless
    of whether the test passed or failed. Without this, a test whose
    assertion fails partway through leaves its background download
    threads running, and they go on to hit a closed database once this
    test's `db` fixture tears down, producing confusing warnings that get
    misattributed to whichever *other* test happens to be running when
    the OS finally delivers the exception.
    """
    from app.database.repositories import HistoryRepository, QueueRepository
    from app.downloader.mock_backend import MockBackend
    from app.queue.manager import QueueManager

    created: list[QueueManager] = []

    def _make(**kwargs):
        mgr = QueueManager(
            queue_repo=QueueRepository(db), history_repo=HistoryRepository(db),
            backend=kwargs.pop("backend", MockBackend(chunk_size=512, total_size=2048)),
            download_folder=str(tmp_path / "downloads"),
            max_concurrent=kwargs.pop("max_concurrent", 2), **kwargs,
        )
        created.append(mgr)
        return mgr

    yield _make

    for mgr in created:
        try:
            mgr.shutdown(timeout=10)
        except Exception:  # noqa: BLE001 - teardown must never mask the real failure
            pass
