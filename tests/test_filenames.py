from datetime import datetime

from app.utils.filenames import (
    build_context,
    render_template,
    sanitize_filename,
    unique_path,
)


def test_sanitize_removes_invalid_chars():
    assert sanitize_filename('bad:name?"<>|*.txt') == "bad_name______.txt"


def test_sanitize_reserved_names():
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("con.txt") == "_con.txt"


def test_sanitize_empty_becomes_untitled():
    assert sanitize_filename("   ") == "untitled"


def test_sanitize_truncates_long_names():
    long_name = "x" * 300
    result = sanitize_filename(long_name)
    assert len(result) <= 150


def test_render_template_basic():
    ctx = build_context("My Cool Video", "SomeUploader", "youtube",
                        datetime(2026, 3, 1), "abc123", "mp4")
    result = render_template("%(uploader)s - %(title)s", ctx)
    assert result == "SomeUploader - My Cool Video"


def test_render_template_sanitizes_each_path_component():
    ctx = build_context('Bad:Title?', "Up|loader", "tiktok", None, "id1", "mp4")
    result = render_template("%(uploader)s/%(title)s", ctx)
    assert "/" in result
    parts = result.split("/")
    assert ":" not in parts[1]
    assert "?" not in parts[1]
    assert "|" not in parts[0]


def test_render_template_unknown_field_becomes_empty():
    ctx = build_context("T", "U", "youtube", None, "id", "mp4")
    result = render_template("%(nonexistent)s%(title)s", ctx)
    assert result == "T"


def test_render_template_value_containing_slash_does_not_create_subfolder():
    """A title like 'Before/After' must not be split into nested folders."""
    ctx = build_context("Before/After", "Uploader", "youtube", None, "id", "mp4")
    result = render_template("%(title)s", ctx)
    assert "/" not in result
    assert result == "Before-After"


def test_unique_path_appends_number(tmp_path):
    p = tmp_path / "video.mp4"
    p.write_text("x")
    result = unique_path(p)
    assert result.name == "video (1).mp4"
    result.write_text("y")
    result2 = unique_path(p)
    assert result2.name == "video (2).mp4"


def test_unique_path_no_conflict(tmp_path):
    p = tmp_path / "fresh.mp4"
    assert unique_path(p) == p
