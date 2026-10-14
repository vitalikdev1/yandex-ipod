# 🎧 Yandex iPod

[![Tests](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml/badge.svg)](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml)
[![Tests](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml)

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Async](https://img.shields.io/badge/async-поддерживается-8A2BE2?style=for-the-badge&logo=python&logoColor=white)](#-флаги-запуска)
[![Языки](https://img.shields.io/badge/язык-RU%20%7C%20EN-blue?style=for-the-badge&logo=googletranslate&logoColor=white)](#-флаги-запуска)
[![Лицензия](https://img.shields.io/badge/лицензия-MIT-green?style=for-the-badge)](#-лицензия)

[![GitHub звезды](https://img.shields.io/github/stars/vitalikdev1/yandex-ipod?style=social)](https://github.com/vitalikdev1/yandex-ipod)
[![GitHub issues](https://img.shields.io/github/issues/vitalikdev1/yandex-ipod)](https://github.com/vitalikdev1/yandex-ipod/issues)


> Скачивает лайкнутые треки из Яндекс.Музыки с полными ID3-тегами, обложками и текстами — готово для iPod, телефона или любого офлайн-плеера.

🇬🇧 [Read in English](README.md)

---

## ✨ Возможности

- 📥 **Массовое скачивание** — забирает все треки из «Мне нравится».
- 🏷 **Полные метаданные** — `TIT2` / `TPE1` / `TALB` + встроенная обложка (`APIC`).
- 📝 **Тексты песен** — пишутся в ID3-фрейм `USLT`, если доступны.
- ⚡ **Sync и async** — выберите под свою сеть (`--async` / `--sync`).
- 🌍 **Двуязычный CLI** — справка и сообщения на русском или английском (`--lang ru|en`).
- 🛡 **Устойчивая сеть** — ретраи на временных сбоях, понятные сообщения для `401`, `403`, `451`.
- ✅ **Покрыто тестами** — 16 unit-тестов, без реальной сети и пауз.
- 🧾 **Идемпотентность** — уже скачанные треки пропускаются.

---

## 🚀 Быстрый старт

### 1. Установка

```bash
git clone https://github.com/vitalikdev1/yandex-ipod.git
cd yandex-ipod

# uv: создаст .venv и поставит зависимости из pyproject.toml
uv sync
```

<details>
<summary>Без <code>uv</code> (pip + venv)</summary>

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e .
```

</details>

### 2. Настройка

Переименуйте `config_example.py` в `config.py`:

```bash
# Windows
ren config_example.py config.py

# Linux / macOS
mv config_example.py config.py
```

Файл добавлен в `.gitignore`, поэтому токен не попадёт в репозиторий.

### 3. Получите токен

OAuth-токен Яндекс.Музыки: <https://oauth.yandex.ru/>.

Положите его в `.env` или прямо в `config.py`:

```env
YANDEX_MUSIC_TOKEN=ваш-токен
```

### 4. Запуск

```bash
# sync, русский (по умолчанию)
python main.py

# async, английский
python main.py --async --lang en

# свой каталог, подробный вывод
python main.py --sync --lang ru -o D:/Music/tracks -v
```

---

## 🎛 Флаги запуска

| Флаг | Описание | По умолчанию |
|---|---|---|
| `--async` | Асинхронный режим (быстрее). | выкл |
| `--sync` | Синхронный режим (стабильнее). | **вкл** |
| `--lang {ru,en}` | Язык сообщений. | авто (`$LANG` → `ru`) |
| `-o, --output PATH` | Куда писать `.mp3`. | `tracks/` |
| `-v, --verbose` | Подробный вывод. | выкл |
| `--version` | Показать версию и выйти. | — |
| `-h, --help` | Справка. | — |

Язык также берётся из окружения:

```bash
YANDEX_IPOD_LANG=en python main.py
```

---

## 🧪 Тесты

```bash
pytest -q
```

```
.........F......                                          [100%]
16 passed in 0.72s
```

Никакой сети и реальных `asyncio.sleep`. Всё на фейках и `tmp_path`.

Что покрыто:

| Слой | Что проверяется |
|---|---|
| `safe_filename` | запрещённые в Windows символы, юникод, пустые строки |
| Sync-пайплайн | скачивание, теги, пропуски, продолжение после ошибки, порядок |
| Async-пайплайн | то же + что `async_sleep` реально инжектится |
| Метаданные | корректная запись `TIT2` / `TPE1` / `TALB` / `APIC` |
| CLI | `--async`, `--sync`, `--lang`, `-o` |

---

## 📁 Структура проекта

```
.
├── main.py              # точка входа, диспетчер sync/async
├── cli.py               # argparse, двухпроходный --lang
├── i18n.py              # переводы (ru / en)
├── client_factory.py    # init клиента + ретраи, обработка 451
├── downloader.py        # TrackDownloader, чистые функции
├── downloaded_db.py     # локальное хранилище «уже скачано»
├── config.py            # токен и настройки
└── tests/
    ├── conftest.py
    ├── test_safe_filename.py
    ├── test_download_sync.py
    └── test_download_async.py
```

---

## 🛡 Обработка ошибок

| HTTP | Что значит | Что происходит |
|---|---|---|
| `401` | Токен невалиден / истёк | `YandexAuthError`, код выхода `2` |
| `403` | Доступ запрещён | `YandexAuthError`, код выхода `2` |
| `451` | Регион / IP заблокированы | `YandexRegionBlocked`, код выхода `3` + подсказка |
| `5xx`, таймауты | Временные | Авто-ретрай с экспоненциальной паузой (4 попытки) |

---

## 🤝 Как помочь проекту

1. Форкните.
2. Ветка: `git checkout -b feature/thing`.
3. Коммит и пуш.
4. Откройте Pull Request.

Перед пушем прогоните `pytest -q` — CI делает то же самое.

---

## 📜 Лицензия

MIT — см. [LICENSE](LICENSE).

---

<p align="center">
  Сделано с ❤️ для тех, кто до сих пор любит свой iPod.
</p>