from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from mutagen.id3 import ID3

import downloader
from downloader import TrackDownloader

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tracks").mkdir(exist_ok=True)

async def test_async_downloads_all(make_track, fake_db, fake_music_tag, tmp_path):
    tracks = [make_track("A", "ArtistA", "AlbumA")]

    d = TrackDownloader(
        db=fake_db,
        output_dir=tmp_path / "tracks",
        async_sleep=AsyncMock(),
    )
    count = await d.download_playlist_async(tracks)

    assert count == 1
    assert (tmp_path / "tracks" / "A.mp3").exists()
    tracks[0].download_async.assert_awaited_once()
    tracks[0].download_cover_async.assert_awaited_once()
    fake_db.mark_downloaded.assert_called_once_with("A", "ArtistA")

async def test_async_skips_existing(make_track, fake_db, fake_music_tag, tmp_path):
    fake_db.is_downloaded.return_value = True
    tracks = [make_track("A", "ArtistA", "AlbumA")]

    d = TrackDownloader(
        db=fake_db,
        output_dir=tmp_path / "tracks",
        async_sleep=AsyncMock(),
    )
    count = await d.download_playlist_async(tracks)

    assert count == 0
    tracks[0].download_async.assert_not_awaited()

async def test_async_continues_after_download_error(make_track, fake_db, fake_music_tag, tmp_path):
    bad = make_track("A", "ArtistA", "AlbumA")
    bad.download_async.side_effect = RuntimeError("network")
    good = make_track("B", "ArtistB", "AlbumB")

    d = TrackDownloader(
        db=fake_db,
        output_dir=tmp_path / "tracks",
        async_sleep=AsyncMock(),
    )
    count = await d.download_playlist_async([bad, good])

    assert count == 1
    assert (tmp_path / "tracks" / "B.mp3").exists()

async def test_async_no_real_sleep(make_track, fake_db, fake_music_tag, tmp_path):
    sleeper = AsyncMock()
    tracks = [make_track("A", "ArtistA", "AlbumA")]

    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks",
                        async_sleep=sleeper)
    await d.download_playlist_async(tracks)

    assert sleeper.await_count >= 2