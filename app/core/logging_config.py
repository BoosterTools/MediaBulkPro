"""Central logging: three separate rotating log files as required by the spec.

logs/application.log - general app lifecycle
logs/downloads.log   - per-download events
logs/errors.log      - errors only, across all loggers
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> logging.Logger:
    root = logging.getLogger()
    if getattr(root, "_mediabulk_configured", False):
        return root
    root.setLevel(level)
    fmt = logging.Formatter(_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    def rotating(filename: str) -> logging.handlers.RotatingFileHandler:
        h = logging.handlers.RotatingFileHandler(
            logs_dir / filename, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        h.setFormatter(fmt)
        return h

    app_handler = rotating("application.log")
    app_handler.addFilter(_MaxLevelFilter(logging.WARNING))
    root.addHandler(app_handler)

    error_handler = rotating("errors.log")
    error_handler.setLevel(logging.ERROR)
    root.addHandler(error_handler)

    downloads_handler = rotating("downloads.log")
    downloads_handler.addFilter(lambda r: r.name.startswith("app.downloader") or
                                r.name.startswith("app.queue"))
    root.addHandler(downloads_handler)

    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)
    root.addHandler(console)

    root._mediabulk_configured = True  # type: ignore[attr-defined]
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
