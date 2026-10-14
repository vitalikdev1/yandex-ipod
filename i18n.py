from __future__ import annotations

import os
from collections.abc import Mapping

DEFAULT_LANG = "ru"
SUPPORTED = ("ru", "en")

TRANSLATIONS: Mapping[str, Mapping[str, str]] = {
    "ru": {
        "program.description": "Скачивание лайкнутых треков из Яндекс.Музыки.",
        "arg.mode": "Режим работы: async (быстрее) или sync (стабильнее).",
        "arg.lang": "Язык сообщений.",
        "arg.output": "Каталог для сохранения треков (по умолчанию: tracks).",
        "arg.verbose": "Подробный вывод.",
        "arg.version": "Показать версию и выйти.",

        "start": "Запуск в режиме {mode}, язык: {lang}",
        "done": "Готово. Скачано треков: {count}",
        "interrupted": "Прервано пользователем.",

        "error.network": "[Сеть] Не удалось подключиться: {err}",
        "error.auth":    "[Авторизация] {err}",
        "error.region":  "[Регион] {err}",
        "error.unknown": "[Ошибка] {err}",

        "net.retry": "Сеть недоступна ({code}), повтор через {delay:.0f}s [{n}/{total}]…",
        "net.giveup": "Не удалось подключиться после {attempts} попыток: {err}",

        "auth.invalid": (
            "Токен Яндекс.Музыки недействителен или истёк. "
            "Получите новый: https://oauth.yandex.ru/"
        ),
        "auth.forbidden": "Доступ запрещён (403). Проверьте права токена и подписку.",
        "region.blocked": (
            "Яндекс.Музыка недоступна из вашего региона/IP (HTTP 451).\n"
            "Что делать:\n"
            "  • отключите VPN/прокси и попробуйте с домашнего интернета;\n"
            "  • если вы за границей — сервис легально недоступен;\n"
            "  • проверьте, что IP не из дата-центра (VPS/хостинг часто блокируется)."
        ),
    },
    "en": {
        "program.description": "Download liked tracks from Yandex Music.",
        "arg.mode": "Execution mode: async (faster) or sync (more stable).",
        "arg.lang": "Message language.",
        "arg.output": "Directory for downloaded tracks (default: tracks).",
        "arg.verbose": "Verbose output.",
        "arg.version": "Show version and exit.",

        "start": "Starting in {mode} mode, language: {lang}",
        "done": "Done. Downloaded tracks: {count}",
        "interrupted": "Interrupted by user.",

        "error.network": "[Network] Could not connect: {err}",
        "error.auth":    "[Auth] {err}",
        "error.region":  "[Region] {err}",
        "error.unknown": "[Error] {err}",

        "net.retry": "Network unavailable ({code}), retrying in {delay:.0f}s [{n}/{total}]…",
        "net.giveup": "Could not connect after {attempts} attempts: {err}",

        "auth.invalid": (
            "Yandex Music token is invalid or expired. "
            "Get a new one: https://oauth.yandex.ru/"
        ),
        "auth.forbidden": "Access denied (403). Check token scopes and subscription.",
        "region.blocked": (
            "Yandex Music is unavailable from your region/IP (HTTP 451).\n"
            "What to do:\n"
            "  • disable VPN/proxy and try a home connection;\n"
            "  • if you are abroad, the service is legally unavailable;\n"
            "  • ensure your IP is not from a datacenter (VPS/hosting is often blocked)."
        ),
    },
}

class Translator:
    def __init__(self, lang: str = DEFAULT_LANG):
        self.set_lang(lang)

    def set_lang(self, lang: str) -> None:
        lang = (lang or "").lower()
        if lang not in SUPPORTED:
            lang = DEFAULT_LANG
        self.lang = lang
        self._table = TRANSLATIONS[lang]

    def __call__(self, key: str, **kwargs) -> str:
        template = self._table.get(key) or TRANSLATIONS[DEFAULT_LANG].get(key, key)
        return template.format(**kwargs) if kwargs else template


def detect_lang(cli_value: str | None) -> str:
    if cli_value:
        return cli_value.lower()
    env = os.environ.get("YANDEX_IPOD_LANG") or os.environ.get("LANG", "")
    env = env.split(".")[0].split("_")[0].lower()
    return env if env in SUPPORTED else DEFAULT_LANG

_ = Translator()
