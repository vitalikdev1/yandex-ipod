# 🎧 Yandex iPod

[![Tests](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml/badge.svg)](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml)
[![Tests](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/vitalikdev1/yandex-ipod/actions/workflows/tests.yml)

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Async](https://img.shields.io/badge/async-supported-8A2BE2?style=for-the-badge&logo=python&logoColor=white)](#-cli-flags)
[![Languages](https://img.shields.io/badge/lang-RU%20%7C%20EN-blue?style=for-the-badge&logo=googletranslate&logoColor=white)](#-cli-flags)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](#-license)

[![GitHub stars](https://img.shields.io/github/stars/vitalikdev1/yandex-ipod?style=social)](https://github.com/vitalikdev1/yandex-ipod)
[![GitHub issues](https://img.shields.io/github/issues/vitalikdev1/yandex-ipod)](https://github.com/vitalikdev1/yandex-ipod/issues)

> Download your liked tracks from Yandex Music with full ID3 tags, cover art and lyrics — ready for your iPod, phone, or any offline player.

🇷🇺 [Читать на русском](README.ru.md)

---

## ✨ Features

- 📥 **Bulk download** — pulls every track from *My Wave → Likes*.
- 🏷 **Full metadata** — `TIT2` / `TPE1` / `TALB` + embedded cover (`APIC`).
- 📝 **Lyrics** — written into the ID3 `USLT` frame when available.
- ⚡ **Sync and async** — pick what fits your network (`--async` / `--sync`).
- 🌍 **Bilingual CLI** — help and messages in Russian or English (`--lang ru|en`).
- 🛡 **Robust networking** — retries on transient errors, clear messages for `401`, `403`, `451`.
- ✅ **Well tested** — 16 unit tests, no real network, no real pauses.
- 🧾 **Idempotent** — tracks already in the DB or on disk are skipped.

---

## 🚀 Quick start

### 1. Install

```bash
git clone https://github.com/vitalikdev1/yandex-ipod.git
cd yandex-ipod

# uv: creates .venv and installs dependencies from pyproject.toml
uv sync
```

<details>
<summary>Without <code>uv</code> (pip + venv)</summary>

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e .
```

</details>

### 2. Configure

Rename `config_example.py` to `config.py`:

```bash
# Windows
ren config_example.py config.py

# Linux / macOS
mv config_example.py config.py
```

The file is git-ignored, so your token never lands in the repository.

### 3. Get a token

Get a Yandex Music OAuth token: <https://oauth.yandex.ru/>.

Put it in `.env` or directly in `config.py`:

```env
YANDEX_MUSIC_TOKEN=your-token-here
```

### 4. Run

```bash
# sync, Russian (default)
python main.py

# async, English
python main.py --async --lang en

# custom output directory, verbose
python main.py --sync --lang ru -o D:/Music/tracks -v
```

---

## 🎛 CLI flags

| Flag | Description | Default |
|---|---|---|
| `--async` | Use the async pipeline (faster). | off |
| `--sync` | Use the sync pipeline (more stable). | **on** |
| `--lang {ru,en}` | Message language. | auto (`$LANG` → `ru`) |
| `-o, --output PATH` | Where `.mp3` files are written. | `tracks/` |
| `-v, --verbose` | Verbose output. | off |
| `--version` | Show version and exit. | — |
| `-h, --help` | Show help. | — |

Language is also picked from the environment:

```bash
YANDEX_IPOD_LANG=en python main.py
```

---

## 🧪 Tests

```bash
pytest -q
```

```
.........F......                                          [100%]
16 passed in 0.72s
```

No network, no real `asyncio.sleep`. Everything runs against fakes and `tmp_path`.

Coverage:

| Layer | What's tested |
|---|---|
| `safe_filename` | Windows-forbidden chars, unicode, empty strings |
| Sync pipeline | downloads, tagging, skips, error recovery, order |
| Async pipeline | same + `async_sleep` is really injected |
| Metadata | `TIT2` / `TPE1` / `TALB` / `APIC` are written correctly |
| CLI | `--async`, `--sync`, `--lang`, `-o` |

---

## 📁 Project layout

```
.
├── main.py              # entry point, dispatch sync/async
├── cli.py               # argparse, two-pass --lang
├── i18n.py              # translations (ru / en)
├── client_factory.py    # Client init + retries, 451 handling
├── downloader.py        # TrackDownloader, pure helpers
├── downloaded_db.py     # local "already downloaded" store
├── config.py            # token & settings
└── tests/
    ├── conftest.py
    ├── test_safe_filename.py
    ├── test_download_sync.py
    └── test_download_async.py
```

---

## 🛡 Error handling

| HTTP | Meaning | What happens |
|---|---|---|
| `401` | Bad / expired token | `YandexAuthError`, exit code `2` |
| `403` | Forbidden | `YandexAuthError`, exit code `2` |
| `451` | Region / IP blocked | `YandexRegionBlocked`, exit code `3` + advice |
| `5xx`, timeouts | Transient | Auto-retry with exponential backoff (4 attempts) |

---

## 🤝 Contributing

1. Fork it.
2. Branch: `git checkout -b feature/thing`.
3. Commit and push.
4. Open a Pull Request.

Run `pytest -q` before pushing — CI runs the same.

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  Made with ❤️ for people who still love their iPod.
</p>