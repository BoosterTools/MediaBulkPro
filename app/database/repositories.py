"""Data-access objects for settings, the download queue, and history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.database.db import Database


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class SettingsRepository:
    DEFAULTS: dict[str, Any] = {
        "theme": "system",
        "language": "en",
        "start_minimized": False,
        "clipboard_monitoring": False,
        "clipboard_auto_download": False,
        "download_folder": "",
        "concurrent_downloads": 4,
        "retry_count": 3,
        "retry_delay_secs": 5,
        "duplicate_behavior": "skip",   # skip | download_again
        "default_quality": "best",
        "default_format": "mp4",
        "audio_only": False,
        "filename_template": "%(uploader)s - %(title)s",
        "folder_structure_by_platform": True,
        "ffmpeg_path": "",
        "speed_limit_kbps": 0,           # 0 = unlimited
        "timeout_secs": 30,
        "show_notifications": True,
    }

    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, key: str, default: Any = None) -> Any:
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (key,))
        if row is None:
            return self.DEFAULTS.get(key, default)
        return json.loads(row["value"])

    def set(self, key: str, value: Any) -> None:
        self.db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )

    def all(self) -> dict[str, Any]:
        merged = dict(self.DEFAULTS)
        for row in self.db.query("SELECT key,value FROM settings"):
            merged[row["key"]] = json.loads(row["value"])
        return merged

    def reset_to_defaults(self) -> None:
        self.db.execute("DELETE FROM settings")


@dataclass
class QueueItem:
    id: int | None
    url: str
    platform: str
    media_type: str
    video_id: str | None = None
    title: str = ""
    uploader: str = ""
    thumbnail_url: str | None = None
    duration_secs: int | None = None
    quality: str = "best"
    output_format: str = "mp4"
    status: str = "queued"
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed_bps: float | None = None
    eta_secs: int | None = None
    output_path: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    position: int = 0
    source_batch: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    @staticmethod
    def from_row(row) -> QueueItem:
        d = dict(row)
        return QueueItem(**d)


class QueueRepository:
    _COLUMNS = [
        "url", "platform", "media_type", "video_id", "title", "uploader", "thumbnail_url",
        "duration_secs", "quality", "output_format", "status", "progress", "downloaded_bytes",
        "total_bytes", "speed_bps", "eta_secs", "output_path", "error_message", "retry_count",
        "position", "source_batch", "created_at", "updated_at",
    ]

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, item: QueueItem) -> int:
        max_pos_row = self.db.query_one("SELECT COALESCE(MAX(position), -1) AS m FROM queue")
        item.position = (max_pos_row["m"] if max_pos_row else -1) + 1
        placeholders = ",".join("?" * len(self._COLUMNS))
        cur = self.db.execute(
            f"INSERT INTO queue({','.join(self._COLUMNS)}) VALUES({placeholders})",
            tuple(getattr(item, c) for c in self._COLUMNS),
        )
        return int(cur.lastrowid)

    def update(self, item_id: int, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        set_clause = ", ".join(f"{k}=?" for k in fields)
        self.db.execute(f"UPDATE queue SET {set_clause} WHERE id=?",
                         (*fields.values(), item_id))

    def get(self, item_id: int) -> QueueItem | None:
        row = self.db.query_one("SELECT * FROM queue WHERE id=?", (item_id,))
        return QueueItem.from_row(row) if row else None

    def all(self) -> list[QueueItem]:
        rows = self.db.query("SELECT * FROM queue ORDER BY position ASC, id ASC")
        return [QueueItem.from_row(r) for r in rows]

    def ids_by_status(self, status: str) -> list[int]:
        rows = self.db.query("SELECT id FROM queue WHERE status=? ORDER BY position ASC, id ASC",
                             (status,))
        return [r["id"] for r in rows]

    def counts_by_status(self) -> dict[str, int]:
        rows = self.db.query("SELECT status, COUNT(*) AS n FROM queue GROUP BY status")
        return {r["status"]: r["n"] for r in rows}

    def remove(self, item_id: int) -> None:
        self.db.execute("DELETE FROM queue WHERE id=?", (item_id,))

    def clear_completed(self) -> int:
        cur = self.db.execute("DELETE FROM queue WHERE status IN ('completed','cancelled')")
        return cur.rowcount

    def find_by_video_id(self, video_id: str) -> QueueItem | None:
        row = self.db.query_one("SELECT * FROM queue WHERE video_id=?", (video_id,))
        return QueueItem.from_row(row) if row else None

    def reorder(self, ordered_ids: list[int]) -> None:
        with self.db.transaction() as conn:
            for pos, item_id in enumerate(ordered_ids):
                conn.execute("UPDATE queue SET position=? WHERE id=?", (pos, item_id))


@dataclass
class HistoryEntry:
    id: int | None
    title: str
    url: str
    platform: str
    video_id: str | None
    date: str
    file_path: str | None
    file_size: int | None
    quality: str | None
    status: str


class HistoryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: HistoryEntry) -> int:
        cur = self.db.execute(
            "INSERT INTO history(title,url,platform,video_id,date,file_path,file_size,quality,status) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (entry.title, entry.url, entry.platform, entry.video_id, entry.date,
             entry.file_path, entry.file_size, entry.quality, entry.status),
        )
        return int(cur.lastrowid)

    def exists_for_video_id(self, video_id: str) -> bool:
        row = self.db.query_one(
            "SELECT 1 FROM history WHERE video_id=? AND status='completed' LIMIT 1", (video_id,)
        )
        return row is not None

    def exists_for_url(self, url: str) -> bool:
        row = self.db.query_one(
            "SELECT 1 FROM history WHERE url=? AND status='completed' LIMIT 1", (url,)
        )
        return row is not None

    def search(
        self, query: str = "", platform: str | None = None, status: str | None = None,
        sort_by: str = "date", descending: bool = True, limit: int = 500,
    ) -> list[dict]:
        sql = "SELECT * FROM history WHERE 1=1"
        params: list[Any] = []
        if query:
            sql += " AND (title LIKE ? OR url LIKE ?)"
            params += [f"%{query}%", f"%{query}%"]
        if platform and platform != "all":
            sql += " AND platform=?"
            params.append(platform)
        if status and status != "all":
            sql += " AND status=?"
            params.append(status)
        sort_col = sort_by if sort_by in {"date", "title", "platform", "file_size"} else "date"
        sql += f" ORDER BY {sort_col} {'DESC' if descending else 'ASC'} LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.db.query(sql, tuple(params))]

    def clear(self) -> None:
        self.db.execute("DELETE FROM history")

    def all_dicts(self) -> list[dict]:
        return [dict(r) for r in self.db.query("SELECT * FROM history ORDER BY date DESC")]
