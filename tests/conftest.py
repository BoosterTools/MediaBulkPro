import pytest

from app.database.db import Database


@pytest.fixture
def db(tmp_path):
    db_dir = tmp_path / "_dbstore"
    db_dir.mkdir()
    database = Database(db_dir / "test.db")
    yield database
    database.close()
