from app.database.repositories import QueueItem, QueueRepository
from app.queue.crash_recovery import discard_all, find_interrupted, resume_all


def test_find_interrupted_detects_mid_flight_statuses(db):
    repo = QueueRepository(db)
    id1 = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    id2 = repo.add(QueueItem(id=None, url="https://b", platform="youtube", media_type="video"))
    id3 = repo.add(QueueItem(id=None, url="https://c", platform="youtube", media_type="video"))
    repo.update(id1, status="downloading")
    repo.update(id2, status="extracting")
    repo.update(id3, status="completed")

    interrupted = find_interrupted(repo)
    assert set(interrupted) == {id1, id2}


def test_resume_all_marks_queued(db):
    repo = QueueRepository(db)
    item_id = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    repo.update(item_id, status="downloading")
    resume_all(repo, [item_id])
    assert repo.get(item_id).status == "queued"


def test_discard_all_marks_cancelled(db):
    repo = QueueRepository(db)
    item_id = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    repo.update(item_id, status="downloading")
    discard_all(repo, [item_id])
    assert repo.get(item_id).status == "cancelled"


def test_no_interrupted_when_clean(db):
    repo = QueueRepository(db)
    item_id = repo.add(QueueItem(id=None, url="https://a", platform="youtube", media_type="video"))
    repo.update(item_id, status="paused")
    assert find_interrupted(repo) == []
