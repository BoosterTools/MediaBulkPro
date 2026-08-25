"""Detects downloads left mid-flight by an unclean shutdown (crash, force-kill).

A clean shutdown (QueueManager.shutdown) always resolves active items to
'paused' before the process exits. Anything still sitting in 'downloading'
or 'extracting' status at the next launch can only mean the app didn't get
a chance to do that — i.e. it crashed or was killed.
"""

from __future__ import annotations

from app.database.repositories import QueueRepository

_INTERRUPTED_STATUSES = ("downloading", "extracting")


def find_interrupted(queue: QueueRepository) -> list[int]:
    ids: list[int] = []
    for status in _INTERRUPTED_STATUSES:
        ids.extend(queue.ids_by_status(status))
    return ids


def resume_all(queue: QueueRepository, ids: list[int]) -> None:
    for item_id in ids:
        queue.update(item_id, status="queued")


def discard_all(queue: QueueRepository, ids: list[int]) -> None:
    for item_id in ids:
        queue.update(item_id, status="cancelled")
