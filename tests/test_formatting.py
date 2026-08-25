import pytest

from app.utils.formatting import human_duration, human_eta, human_size, human_speed


@pytest.mark.parametrize("n,expected", [
    (None, "—"), (0, "0 B"), (1024, "1.0 KB"), (1024**3, "1.0 GB"),
])
def test_human_size(n, expected):
    assert human_size(n) == expected


def test_human_size_negative_raises():
    with pytest.raises(ValueError):
        human_size(-1)


def test_human_speed():
    assert human_speed(None) == "—"
    assert human_speed(0) == "—"
    assert human_speed(1024) == "1.0 KB/s"


def test_human_eta():
    assert human_eta(None) == "—"
    assert human_eta(45) == "45s"
    assert human_eta(125) == "2m 5s"
    assert human_eta(3725) == "1h 2m"


def test_human_duration():
    assert human_duration(None) == "—"
    assert human_duration(65) == "1:05"
    assert human_duration(3661) == "1:01:01"
