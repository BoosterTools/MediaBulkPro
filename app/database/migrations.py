"""Ordered schema migrations. Append new entries; never edit applied ones."""

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS queue (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            url            TEXT NOT NULL,
            platform       TEXT NOT NULL,
            media_type     TEXT NOT NULL,
            video_id       TEXT,
            title          TEXT,
            uploader       TEXT,
            thumbnail_url  TEXT,
            duration_secs  INTEGER,
            quality        TEXT NOT NULL DEFAULT 'best',
            output_format  TEXT NOT NULL DEFAULT 'mp4',
            status         TEXT NOT NULL DEFAULT 'queued',
            progress       REAL NOT NULL DEFAULT 0,
            downloaded_bytes INTEGER NOT NULL DEFAULT 0,
            total_bytes    INTEGER,
            speed_bps      REAL,
            eta_secs       INTEGER,
            output_path    TEXT,
            error_message  TEXT,
            retry_count    INTEGER NOT NULL DEFAULT 0,
            position       INTEGER NOT NULL DEFAULT 0,
            source_batch   TEXT,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
        CREATE INDEX IF NOT EXISTS idx_queue_video_id ON queue(video_id);

        CREATE TABLE IF NOT EXISTS history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT,
            url           TEXT NOT NULL,
            platform      TEXT NOT NULL,
            video_id      TEXT,
            date          TEXT NOT NULL,
            file_path     TEXT,
            file_size     INTEGER,
            quality       TEXT,
            status        TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_history_platform ON history(platform);
        CREATE INDEX IF NOT EXISTS idx_history_status ON history(status);
        CREATE INDEX IF NOT EXISTS idx_history_video_id ON history(video_id);
        CREATE INDEX IF NOT EXISTS idx_history_date ON history(date);
        """,
    ),
]
