import hashlib
import json
from pathlib import Path

DB_PATH = Path("downloaded.json")

def _normalize_artist(artist) -> str:
    if isinstance(artist, (list, tuple)):
        return ", ".join(str(a) for a in artist)
    return str(artist)

def _hash_track(title: str, artist) -> str:
    artist = _normalize_artist(artist)
    raw = f"{title.strip().lower()}|{artist.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def load_db() -> dict:
    if DB_PATH.exists():
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db: dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def is_downloaded(title: str, artist) -> bool:
    db = load_db()
    h = _hash_track(title, artist)
    return h in db

def mark_downloaded(title: str, artist):
    db = load_db()
    h = _hash_track(title, artist)
    db[h] = {"title": title, "artist": _normalize_artist(artist)}
    save_db(db)
