from unittest.mock import MagicMock

import pytest
from mutagen.id3 import ID3

import downloader
from downloader import TrackDownloader


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tracks").mkdir(exist_ok=True)

def test_downloads_all_and_writes_tags(make_track, fake_db, fake_music_tag, tmp_path):
    tracks = [
        make_track("A", "ArtistA", "AlbumA"),
        make_track("B", "ArtistB", "AlbumB"),
    ]

    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks")
    count = d.download_playlist(tracks)

    assert count == 2
    assert (tmp_path / "tracks" / "A.mp3").exists()
    assert (tmp_path / "tracks" / "B.mp3").exists()
    assert not (tmp_path / "tracks" / "A.jpg").exists()

    audio = ID3(str(tmp_path / "tracks" / "A.mp3"))
    assert audio["TIT2"].text[0] == "A"
    assert audio["TPE1"].text[0] == "ArtistA"
    assert audio["TALB"].text[0] == "AlbumA"
    assert audio.getall("APIC"), "APIC must be installed."

    assert fake_db.mark_downloaded.call_count == 2
    fake_db.mark_downloaded.assert_any_call("A", "ArtistA")

def test_skips_already_downloaded(make_track, fake_db, fake_music_tag, tmp_path):
    fake_db.is_downloaded.return_value = True
    tracks = [make_track("A", "ArtistA", "AlbumA")]

    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks")
    count = d.download_playlist(tracks)

    assert count == 0
    tracks[0].download.assert_not_called()
    fake_db.mark_downloaded.assert_not_called()

def test_skips_if_file_exists(make_track, fake_db, fake_music_tag, tmp_path):
    (tmp_path / "tracks").mkdir(exist_ok=True)
    (tmp_path / "tracks" / "A.mp3").write_bytes(b"")

    tracks = [make_track("A", "ArtistA", "AlbumA")]
    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks")
    count = d.download_playlist(tracks)

    assert count == 0
    tracks[0].download.assert_not_called()

def test_continues_after_download_error(make_track, fake_db, fake_music_tag, tmp_path):
    bad = make_track("A", "ArtistA", "AlbumA")
    bad.download.side_effect = RuntimeError("network")
    good = make_track("B", "ArtistB", "AlbumB")

    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks")
    count = d.download_playlist([bad, good])

    assert count == 1
    good.download.assert_called_once()
    assert (tmp_path / "tracks" / "B.mp3").exists()

def test_module_level_function_still_works(make_track, fake_db, fake_music_tag, tmp_path):
    client = MagicMock()
    likes = MagicMock()
    likes.fetch_tracks.return_value = [make_track("A", "ArtistA", "AlbumA")]
    client.users_likes_tracks.return_value = likes

    count = downloader.download_playlist(client, db=fake_db, output_dir=tmp_path / "tracks")
    assert count == 1
    assert (tmp_path / "tracks" / "A.mp3").exists()

def test_processes_in_reverse_order(make_track, fake_db, fake_music_tag, tmp_path):
    order = []
    a = make_track("A", "ArtistA", "AlbumA")
    b = make_track("B", "ArtistB", "AlbumB")

    a_orig = a.download.side_effect
    b_orig = b.download.side_effect

    def make_recorder(label, orig):
        def _side_effect(path, *args, **kwargs):
            order.append(label)
            return orig(path, *args, **kwargs)
        return _side_effect

    a.download.side_effect = make_recorder("A", a_orig)
    b.download.side_effect = make_recorder("B", b_orig)

    d = TrackDownloader(db=fake_db, output_dir=tmp_path / "tracks")
    d.download_playlist([a, b])

    assert order == ["B", "A"]