from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def make_track(tmp_path):
    def _make(title="Song", artist="Artist", album="Album", lyrics="Some lyrics"):
        t = MagicMock()
        t.title = title
        t.artists_name.return_value = artist
        t.albums = [MagicMock(title=album)]

        def fake_download(path):
            Path(path).write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00\x00\x00")

        def fake_cover(path):
            Path(path).write_bytes(b"\xff\xd8\xff\xe0fake_jpeg_bytes")

        t.download.side_effect = fake_download
        t.download_cover.side_effect = fake_cover

        # async
        t.download_async = AsyncMock(side_effect=fake_download)
        t.download_cover_async = AsyncMock(side_effect=fake_cover)

        lyrics_obj = MagicMock()
        lyrics_obj.fetch_lyrics.return_value = lyrics
        lyrics_obj.fetch_lyrics_async = AsyncMock(return_value=lyrics)
        t.get_lyrics.return_value = lyrics_obj
        t.get_lyrics_async = AsyncMock(return_value=lyrics_obj)

        return t
    return _make


@pytest.fixture
def fake_db(monkeypatch):
    db = MagicMock()
    db.is_downloaded.return_value = False
    return db


@pytest.fixture
def fake_music_tag(monkeypatch):
    store = {}
    def load_file(path):
        obj = MagicMock()
        obj.__setitem__ = lambda self, k, v: store.__setitem__(k, v)
        obj.save = MagicMock()
        return obj
    module = MagicMock()
    module.load_file.side_effect = load_file
    monkeypatch.setitem(__import__("sys").modules, "music_tag", module)
    return module
