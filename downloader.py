"""Download liked Yandex Music tracks with full metadata tagging.

The module is structured for testability:

* Pure helpers (``safe_filename``, ``_album_title``, ``apply_metadata``)
  perform no I/O and can be tested directly.
* :class:`TrackDownloader` receives every external dependency through its
  constructor (``db``, ``output_dir``, ``async_sleep``), so tests can inject
  fakes without monkey-patching module globals.
* The sync and async code paths share the same metadata logic.

The module-level helpers :func:`download_playlist` /
:func:`download_playlist_async` / :func:`main` are kept for backwards
compatibility with the original script.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path

import music_tag
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, ID3NoHeaderError
from yandex_music import Client, ClientAsync

import downloaded_db as default_db
from config import YANDEX_MUSIC_TOKEN

log = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("tracks")

# Delays used by the async pipeline to be polite with the API.
SKIP_DELAY = 0.5
PRE_DOWNLOAD_DELAY = 2.0
POST_DOWNLOAD_DELAY = 1.0


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def safe_filename(name: str) -> str:
    """Strip characters that are not allowed in file names."""
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()


def _album_title(track) -> str | None:
    """Return the first album title or ``None`` if the track has none."""
    albums = getattr(track, "albums", None)
    if not albums:
        return None
    try:
        return albums[0].title
    except (AttributeError, IndexError, TypeError):
        return None

def apply_metadata(
    path: Path,
    *,
    title: str,
    artist: str,
    album: str | None,
    lyrics: str | None,
    cover_path: Path | None = None,
) -> None:
    """Write lyrics + ID3 tags (including cover) to an mp3 file."""
    # 1. Lyrics via music_tag (best effort, never fail the download).
    if lyrics:
        try:
            tagged = music_tag.load_file(str(path))
            tagged["lyrics"] = lyrics
            tagged.save()
        except Exception as e: # noqa: BLE001
            log.debug("Не удалось записать текст для '%s': %s", path.name, e)

    # 2. ID3 tags via mutagen.
    try:
        audio = ID3(str(path))
    except ID3NoHeaderError:
        audio = ID3()

    audio.delall("TIT2")
    audio.add(TIT2(encoding=3, text=title))

    audio.delall("TPE1")
    audio.add(TPE1(encoding=3, text=artist))

    if album:
        audio.delall("TALB")
        audio.add(TALB(encoding=3, text=album))

    if cover_path is not None and cover_path.exists():
        with open(cover_path, "rb") as img:
            audio.delall("APIC")
            audio.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img.read(),
            ))

    audio.save(str(path), v2_version=3)

# --------------------------------------------------------------------------- #
# Downloader
# --------------------------------------------------------------------------- #

class TrackDownloader:
    """Download tracks and apply metadata.

    Parameters
    ----------
    db:
        Object with ``is_downloaded(title, artist)`` and
        ``mark_downloaded(title, artist)`` (see :mod:`downloaded_db`).
        Defaults to the ``downloaded_db`` module itself.
    output_dir:
        Directory where ``.mp3`` files are written. Created if missing.
    async_sleep:
        Awaitable used for the async pipeline's delays. Tests usually pass
        a no-op ``AsyncMock`` to avoid real pauses.
    """

    def __init__(
        self,
        db=None,
        output_dir=DEFAULT_OUTPUT_DIR,
        async_sleep=asyncio.sleep,
    ):
        self.db = db if db is not None else default_db
        self.output_dir = Path(output_dir)
        self.async_sleep = async_sleep
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #

    def _paths(self, name: str):
        return (
            self.output_dir / f"{name}.mp3",
            self.output_dir / f"{name}.jpg",
        )

    def _should_skip(self, title: str, artist: str, file_path: Path) -> bool:
        return self.db.is_downloaded(title, artist) or file_path.exists()

    def _finalize(
        self,
        track,
        mp3_path: Path,
        jpg_path: Path,
        lyrics: str | None,
    ) -> None:
        """Apply metadata and remove the temporary cover file."""
        try:
            apply_metadata(
                mp3_path,
                title=safe_filename(track.title),
                artist=track.artists_name(),
                album=_album_title(track),
                lyrics=lyrics,
                cover_path=jpg_path,
            )
        finally:
            if jpg_path.exists():
                try:
                    os.remove(jpg_path)
                except OSError:
                    pass

    @staticmethod
    def _fetch_lyrics_sync(track) -> str | None:
        try:
            return track.get_lyrics().fetch_lyrics()
        except Exception as e: # noqa: BLE001
            log.debug("Нет текста для '%s': %s", track.title, e)
            return None

    @staticmethod
    async def _fetch_lyrics_async(track) -> str | None:
        try:
            lyrics_obj = await track.get_lyrics_async()
            return await lyrics_obj.fetch_lyrics_async()
        except Exception as e: # noqa: BLE001
            log.debug("Нет текста для '%s': %s", track.title, e)
            return None

    # ------------------------------------------------------------------ #
    # Sync pipeline
    # ------------------------------------------------------------------ #

    def process_sync(self, track) -> bool:
        """Download and tag a single track. Returns True if downloaded."""
        name = safe_filename(track.title)
        artist = track.artists_name()
        mp3_path, jpg_path = self._paths(name)

        if self._should_skip(track.title, artist, mp3_path):
            print(f"Пропуск (уже в базе): {track.title}")
            return False

        print(f"Скачивание: {track.title}")
        try:
            track.download(str(mp3_path))
        except Exception as e: # noqa: BLE001
            print(f"Ошибка скачивания '{track.title}': {e}")
            return False

        try:
            track.download_cover(str(jpg_path))
        except Exception as e: # noqa: BLE001
            # Cover failure must not skip the whole track.
            print(f"Ошибка обложки '{track.title}': {e}")

        lyrics = self._fetch_lyrics_sync(track)
        self._finalize(track, mp3_path, jpg_path, lyrics)

        self.db.mark_downloaded(track.title, artist)
        print(f"Песня '{name}' скачана.\n")
        return True

    def download_playlist(self, tracks) -> int:
        """Download tracks in reverse order. Returns number downloaded."""
        downloaded = 0
        for i in range(len(tracks) - 1, -1, -1):
            if self.process_sync(tracks[i]):
                downloaded += 1
        return downloaded

    # ------------------------------------------------------------------ #
    # Async pipeline
    # ------------------------------------------------------------------ #

    async def process_async(self, track) -> bool:
        name = safe_filename(track.title)
        artist = track.artists_name()
        mp3_path, jpg_path = self._paths(name)

        if self._should_skip(track.title, artist, mp3_path):
            print(f"Пропуск (уже в базе): {track.title}")
            await self.async_sleep(SKIP_DELAY)
            return False

        print(f"Скачивание: {track.title}")
        await self.async_sleep(PRE_DOWNLOAD_DELAY)

        try:
            await track.download_async(str(mp3_path))
        except Exception as e: # noqa: BLE001
            print(f"Ошибка скачивания '{track.title}': {e}")
            return False

        try:
            await track.download_cover_async(str(jpg_path))
        except Exception as e: # noqa: BLE001
            print(f"Ошибка обложки '{track.title}': {e}")

        lyrics = await self._fetch_lyrics_async(track)
        self._finalize(track, mp3_path, jpg_path, lyrics)

        self.db.mark_downloaded(track.title, artist)
        print(f"Песня '{name}' скачана.\n")
        await self.async_sleep(POST_DOWNLOAD_DELAY)
        return True

    async def download_playlist_async(self, tracks) -> int:
        downloaded = 0
        for i in range(len(tracks) - 1, -1, -1):
            if await self.process_async(tracks[i]):
                downloaded += 1
        return downloaded


# --------------------------------------------------------------------------- #
# Backwards-compatible module-level API
# --------------------------------------------------------------------------- #

def download_playlist(client, db=None, output_dir=DEFAULT_OUTPUT_DIR) -> int:
    likes = client.users_likes_tracks()
    tracks = likes.fetch_tracks()
    downloader = TrackDownloader(db=db, output_dir=output_dir)
    return downloader.download_playlist(tracks)


async def download_playlist_async(client, db=None, output_dir=DEFAULT_OUTPUT_DIR) -> int:
    likes = await client.users_likes_tracks()
    tracks = await likes.fetch_tracks_async()
    downloader = TrackDownloader(db=db, output_dir=output_dir)
    return await downloader.download_playlist_async(tracks)


async def main_async():
    client = await ClientAsync(YANDEX_MUSIC_TOKEN).init()
    await download_playlist_async(client)


def main():
    client = Client(YANDEX_MUSIC_TOKEN).init()
    download_playlist(client)


if __name__ == "__main__":
    main()