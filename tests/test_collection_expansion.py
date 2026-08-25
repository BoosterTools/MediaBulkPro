import pytest

from app.downloader.mock_backend import MockBackend
from app.downloader.models import CollectionEntry
from app.queue.collection_expansion import NotACollectionError, expand_collection


def test_expand_youtube_channel():
    backend = MockBackend(collections={
        "https://www.youtube.com/@SomeChannel": [
            CollectionEntry(url="https://youtu.be/vid1", title="First"),
            CollectionEntry(url="https://youtu.be/vid2", title="Second"),
        ]
    })
    match, entries = expand_collection("https://www.youtube.com/@SomeChannel", backend)
    assert match.is_collection
    assert len(entries) == 2
    assert entries[0].title == "First"


def test_expand_instagram_profile():
    backend = MockBackend(collections={
        "https://www.instagram.com/someuser/": [
            CollectionEntry(url="https://instagram.com/reel/abc", title="Reel 1"),
        ]
    })
    match, entries = expand_collection("https://www.instagram.com/someuser/", backend)
    assert match.is_collection
    assert len(entries) == 1


def test_expand_tiktok_profile():
    backend = MockBackend(collections={
        "https://www.tiktok.com/@someuser": [
            CollectionEntry(url="https://www.tiktok.com/@someuser/video/123", title="TT vid"),
        ]
    })
    match, entries = expand_collection("https://www.tiktok.com/@someuser", backend)
    assert match.is_collection
    assert len(entries) == 1


def test_expand_single_video_raises():
    backend = MockBackend()
    with pytest.raises(NotACollectionError):
        expand_collection("https://youtu.be/singlevideo1", backend)


def test_expand_unknown_collection_returns_empty():
    backend = MockBackend()  # no entries registered for this URL
    match, entries = expand_collection("https://www.youtube.com/@EmptyChannel", backend)
    assert entries == []
