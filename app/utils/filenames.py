"""Filename sanitization and template rendering for downloaded media.

Windows-safe by construction: strips reserved characters/names and enforces
a maximum component length, then guarantees uniqueness against whatever is
already on disk.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_MAX_COMPONENT_LEN = 150


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Make *name* safe as a single Windows path component (no separators)."""
    name = _INVALID_CHARS.sub(replacement, name).strip().rstrip(".")
    if not name:
        name = "untitled"
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = f"_{name}"
    if len(name) > _MAX_COMPONENT_LEN:
        name = name[:_MAX_COMPONENT_LEN].rstrip()
    return name


def sanitize_folder_component(name: str) -> str:
    return sanitize_filename(name)


TEMPLATE_FIELDS = {"title", "uploader", "platform", "upload_date", "id", "ext"}


def render_template(template: str, context: dict[str, str]) -> str:
    """Render a ``%(field)s``-style template (mirrors yt-dlp's own syntax).

    Field values are sanitized *before* substitution so a value that itself
    contains ``/`` (a perfectly normal character in a video title) can never
    introduce accidental subfolders — only literal ``/`` in the template
    string itself defines folder structure. Unknown fields resolve to an
    empty string rather than raising, so a typo in a user-configured
    template never crashes a whole batch.
    """
    def replace(match: re.Match[str]) -> str:
        field = match.group(1)
        value = str(context.get(field, ""))
        return value.replace("/", "-").replace("\\", "-")

    rendered = re.sub(r"%\((\w+)\)s", replace, template)
    parts = [sanitize_filename(p) for p in rendered.split("/")]
    return "/".join(p for p in parts if p)


def unique_path(path: Path) -> Path:
    """Append ' (1)', ' (2)', ... if *path* already exists."""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def build_context(
    title: str, uploader: str, platform: str, upload_date: datetime | None,
    video_id: str, ext: str,
) -> dict[str, str]:
    return {
        "title": title or "untitled", "uploader": uploader or "unknown",
        "platform": platform, "id": video_id or "",
        "upload_date": upload_date.strftime("%Y-%m-%d") if upload_date else "",
        "ext": ext,
    }
