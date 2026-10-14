from __future__ import annotations

import asyncio
import re
import time

from yandex_music import Client, ClientAsync
from yandex_music.exceptions import NetworkError

from config import YANDEX_MUSIC_TOKEN
from i18n import Translator

STATUS_RE = re.compile(r"\((\d{3})\)")
FATAL_STATUSES = {401, 403, 451}
RETRY_ATTEMPTS = 4
RETRY_BASE_DELAY = 2.0
RETRY_MAX_DELAY = 30.0

class YandexAuthError(RuntimeError): ...
class YandexRegionBlocked(RuntimeError): ...

def _status_code(exc: NetworkError) -> int | None:
    m = STATUS_RE.search(str(exc))
    return int(m.group(1)) if m else None

def _explain(exc: NetworkError, t: Translator) -> None:
    code = _status_code(exc)
    if code == 401:
        raise YandexAuthError(t("auth.invalid")) from exc
    if code == 403:
        raise YandexAuthError(t("auth.forbidden")) from exc
    if code == 451:
        raise YandexRegionBlocked(t("region.blocked")) from exc

def _with_retries(func, t: Translator, *, attempts: int = RETRY_ATTEMPTS):
    last = None
    for i in range(attempts):
        try:
            return func()
        except NetworkError as e:
            code = _status_code(e)
            if code in FATAL_STATUSES:
                _explain(e, t)
            last = e
            if i == attempts - 1:
                break
            delay = min(RETRY_BASE_DELAY * (2 ** i), RETRY_MAX_DELAY)
            print(t("net.retry", code=code or "?", delay=delay,
                    n=i + 1, total=attempts))
            time.sleep(delay)
    raise NetworkError(t("net.giveup", attempts=attempts, err=last))

async def _with_retries_async(factory, t: Translator, *,
                              attempts: int = RETRY_ATTEMPTS):
    last = None
    for i in range(attempts):
        try:
            return await factory()
        except NetworkError as e:
            code = _status_code(e)
            if code in FATAL_STATUSES:
                _explain(e, t)
            last = e
            if i == attempts - 1:
                break
            delay = min(RETRY_BASE_DELAY * (2 ** i), RETRY_MAX_DELAY)
            print(t("net.retry", code=code or "?", delay=delay,
                    n=i + 1, total=attempts))
            await asyncio.sleep(delay)
    raise NetworkError(t("net.giveup", attempts=attempts, err=last))

def build_client(t: Translator) -> Client:
    return _with_retries(lambda: Client(YANDEX_MUSIC_TOKEN).init(), t)

async def build_client_async(t: Translator) -> ClientAsync:
    return await _with_retries_async(
        lambda: ClientAsync(YANDEX_MUSIC_TOKEN).init(), t
    )
