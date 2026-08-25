from app.database.repositories import (
    HistoryEntry,
    HistoryRepository,
    QueueItem,
    QueueRepository,
    SettingsRepository,
)


def test_settings_defaults_and_persistence(db):
    s = SettingsRepository(db)
    assert s.get("concurrent_downloads") == 4
    assert s.get("duplicate_behavior") == "skip"
    s.set("concurrent_downloads", 8)
    assert s.get("concurrent_downloads") == 8
    assert s.all()["retry_count"] == 3


def test_settings_reset(db):
    s = SettingsRepository(db)
    s.set("theme", "dark")
    s.reset_to_defaults()
    assert s.get("theme") == "system"


def test_queue_add_and_position_ordering(db):
    repo = QueueRepository(db)
    id1 = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    id2 = repo.add(QueueItem(id=None, url="https://b", platform="tiktok", media_type="video"))
    items = repo.all()
    assert [i.id for i in items] == [id1, id2]
    assert items[0].position == 0
    assert items[1].position == 1


def test_queue_update_and_status_counts(db):
    repo = QueueRepository(db)
    item_id = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    repo.update(item_id, status="downloading", progress=50.0)
    fetched = repo.get(item_id)
    assert fetched.status == "downloading"
    assert fetched.progress == 50.0
    counts = repo.counts_by_status()
    assert counts["downloading"] == 1


def test_queue_reorder(db):
    repo = QueueRepository(db)
    ids = [repo.add(QueueItem(id=None, url=f"https://{i}", platform="youtube", media_type="video"))
           for i in range(3)]
    repo.reorder([ids[2], ids[0], ids[1]])
    ordered = [i.id for i in repo.all()]
    assert ordered == [ids[2], ids[0], ids[1]]


def test_queue_find_by_video_id(db):
    repo = QueueRepository(db)
    item = QueueItem(id=None, url="https://a", platform="youtube", media_type="video",
                     video_id="vid123")
    repo.add(item)
    found = repo.find_by_video_id("vid123")
    assert found is not None
    assert repo.find_by_video_id("missing") is None


def test_queue_clear_completed(db):
    repo = QueueRepository(db)
    id1 = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    id2 = repo.add(QueueItem(id=None, url="https://b", platform="youtube", media_type="video"))
    repo.update(id1, status="completed")
    repo.update(id2, status="queued")
    removed = repo.clear_completed()
    assert removed == 1
    assert len(repo.all()) == 1


def test_history_add_and_dedup_checks(db):
    repo = HistoryRepository(db)
    repo.add(HistoryEntry(id=None, title="T", url="https://a", platform="youtube",
                          video_id="vid1", date="2026-01-01", file_path="/x/T.mp4",
                          file_size=1000, quality="1080p", status="completed"))
    assert repo.exists_for_video_id("vid1")
    assert repo.exists_for_url("https://a")
    assert not repo.exists_for_video_id("other")


def test_history_search_filters(db):
    repo = HistoryRepository(db)
    repo.add(HistoryEntry(id=None, title="Cats Compilation", url="https://a", platform="youtube",
                          video_id="v1", date="2026-01-01", file_path=None, file_size=None,
                          quality="1080p", status="completed"))
    repo.add(HistoryEntry(id=None, title="Dogs Video", url="https://b", platform="tiktok",
                          video_id="v2", date="2026-01-02", file_path=None, file_size=None,
                          quality="best", status="failed"))
    assert len(repo.search(query="cats")) == 1
    assert len(repo.search(platform="tiktok")) == 1
    assert len(repo.search(status="failed")) == 1
    assert len(repo.search()) == 2


def test_history_clear(db):
    repo = HistoryRepository(db)
    repo.add(HistoryEntry(id=None, title="T", url="https://a", platform="youtube", video_id="v1",
                          date="2026-01-01", file_path=None, file_size=None, quality="best",
                          status="completed"))
    repo.clear()
    assert repo.all_dicts() == []
