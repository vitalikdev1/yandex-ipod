from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from yandex_music.exceptions import NetworkError

from cli import parse_args
from client_factory import (
    build_client,
    build_client_async,
    YandexAuthError,
    YandexRegionBlocked,
)
from downloader import TrackDownloader
from i18n import Translator

def _print_fatal(err: BaseException, t: Translator) -> int:
    if isinstance(err, YandexRegionBlocked):
        print(t("error.region", err=err))
        return 3
    if isinstance(err, YandexAuthError):
        print(t("error.auth", err=err))
        return 2
    if isinstance(err, NetworkError):
        print(t("error.network", err=err))
        return 1
    print(t("error.unknown", err=err))
    return 1

def run_sync(opts, t: Translator) -> int:
    client = build_client(t)
    likes = client.users_likes_tracks()
    tracks = likes.fetch_tracks()
    downloader = TrackDownloader(output_dir=opts.output_dir)
    downloaded = downloader.download_playlist(tracks)
    print(t("done", count=downloaded))
    return 0

async def run_async(opts, t: Translator) -> int:
    client = await build_client_async(t)
    likes = await client.users_likes_tracks()
    tracks = await likes.fetch_tracks_async()
    downloader = TrackDownloader(output_dir=opts.output_dir)
    downloaded = await downloader.download_playlist_async(tracks)
    print(t("done", count=downloaded))
    return 0

def main(argv: list[str] | None = None) -> int:
    opts = parse_args(argv)
    t = Translator(opts.lang)

    print(t("start", mode="async" if opts.use_async else "sync",
            lang=opts.lang))

    try:
        if opts.use_async:
            return asyncio.run(run_async(opts, t))
        return run_sync(opts, t)
    except KeyboardInterrupt:
        print("\n" + t("interrupted"))
        return 130
    except (YandexAuthError, YandexRegionBlocked, NetworkError) as e:
        return _print_fatal(e, t)

if __name__ == "__main__":
    sys.exit(main())