"""Human-friendly formatting helpers for sizes, speeds, and durations."""

from __future__ import annotations

_UNITS = ("B", "KB", "MB", "GB", "TB")


def human_size(num_bytes: float | None, decimals: int = 1) -> str:
    if num_bytes is None:
        return "—"
    if num_bytes < 0:
        raise ValueError("size cannot be negative")
    value = float(num_bytes)
    for unit in _UNITS:
        if value < 1024 or unit == _UNITS[-1]:
            return f"{int(value)} B" if unit == "B" else f"{value:.{decimals}f} {unit}"
        value /= 1024
    return f"{value:.{decimals}f} TB"


def human_speed(bytes_per_sec: float | None) -> str:
    if not bytes_per_sec:
        return "—"
    return f"{human_size(bytes_per_sec)}/s"


def human_eta(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def human_duration(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
