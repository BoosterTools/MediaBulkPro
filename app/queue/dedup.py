"""Duplicate detection: checks a candidate URL/video-id against history
before it gets downloaded again."""

from __future__ import annotations

from app.database.repositories import HistoryRepository, QueueRepository


def is_duplicate(video_id: str | None, url: str, history: HistoryRepository) -> bool:
    if video_id and history.exists_for_video_id(video_id):
        return True
    return history.exists_for_url(url)


def is_already_queued(video_id: str | None, queue: QueueRepository) -> bool:
    if not video_id:
        return False
    existing = queue.find_by_video_id(video_id)
    return existing is not None and existing.status not in ("failed", "cancelled")
