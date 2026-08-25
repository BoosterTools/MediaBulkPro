from app.platforms.detector import deduplicate_urls, detect, detect_many
from app.platforms.models import MediaType, Platform


def test_youtube_watch_url():
    m = detect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert m.platform == Platform.YOUTUBE
    assert m.media_type == MediaType.VIDEO
    assert m.video_id == "dQw4w9WgXcQ"


def test_youtube_short_host():
    m = detect("https://youtu.be/dQw4w9WgXcQ")
    assert m.platform == Platform.YOUTUBE
    assert m.media_type == MediaType.VIDEO
    assert m.video_id == "dQw4w9WgXcQ"


def test_youtube_shorts():
    m = detect("https://www.youtube.com/shorts/abc123XYZ_9")
    assert m.platform == Platform.YOUTUBE
    assert m.media_type == MediaType.SHORT
    assert m.video_id == "abc123XYZ_9"


def test_youtube_playlist():
    m = detect("https://www.youtube.com/playlist?list=PLabcdefghijklmno")
    assert m.platform == Platform.YOUTUBE
    assert m.media_type == MediaType.PLAYLIST


def test_youtube_channel_variants():
    for url in [
        "https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx",
        "https://www.youtube.com/c/SomeChannel",
        "https://www.youtube.com/@SomeHandle",
        "https://www.youtube.com/user/legacyuser",
    ]:
        m = detect(url)
        assert m.platform == Platform.YOUTUBE
        assert m.media_type == MediaType.CHANNEL, url
        assert m.is_collection


def test_instagram_reel():
    m = detect("https://www.instagram.com/reel/Cabc123XYZ/")
    assert m.platform == Platform.INSTAGRAM
    assert m.media_type == MediaType.REEL
    assert m.video_id == "Cabc123XYZ"


def test_instagram_post():
    m = detect("https://www.instagram.com/p/Cabc123XYZ/")
    assert m.platform == Platform.INSTAGRAM
    assert m.media_type == MediaType.VIDEO


def test_instagram_profile_is_collection():
    m = detect("https://www.instagram.com/someuser/")
    assert m.platform == Platform.INSTAGRAM
    assert m.media_type == MediaType.CHANNEL
    assert m.is_collection


def test_tiktok_video():
    m = detect("https://www.tiktok.com/@someuser/video/7123456789012345678")
    assert m.platform == Platform.TIKTOK
    assert m.media_type == MediaType.VIDEO
    assert m.video_id == "7123456789012345678"


def test_tiktok_profile_is_collection():
    m = detect("https://www.tiktok.com/@someuser")
    assert m.platform == Platform.TIKTOK
    assert m.media_type == MediaType.CHANNEL
    assert m.is_collection


def test_tiktok_short_link_host():
    m = detect("https://vm.tiktok.com/ZMabcdefg/")
    assert m.platform == Platform.TIKTOK
    assert m.media_type == MediaType.VIDEO


def test_unknown_url():
    m = detect("https://example.com/not-a-video")
    assert m.platform == Platform.UNKNOWN
    assert not m.is_supported


def test_empty_and_garbage_input():
    assert detect("").platform == Platform.UNKNOWN
    assert detect("not a url at all").platform == Platform.UNKNOWN


def test_detect_many():
    urls = ["https://youtu.be/abc123defgh", "https://www.tiktok.com/@u/video/123456789012345"]
    results = detect_many(urls)
    assert len(results) == 2
    assert results[0].platform == Platform.YOUTUBE
    assert results[1].platform == Platform.TIKTOK


def test_deduplicate_urls_preserves_order_and_trailing_slash():
    urls = [
        "https://youtu.be/abc", "https://youtu.be/xyz", "https://youtu.be/abc",
        "https://youtu.be/xyz/", "  ", "https://youtu.be/abc",
    ]
    result = deduplicate_urls(urls)
    assert result == ["https://youtu.be/abc", "https://youtu.be/xyz"]
