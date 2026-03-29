"""Local JSON-based state persistence.

State files live in data/ (gitignored). Drive is used only for file storage.
"""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"


def _path(filename: str) -> Path:
    _DATA_DIR.mkdir(exist_ok=True)
    return _DATA_DIR / filename


def load(filename: str) -> dict:
    p = _path(filename)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save(filename: str, data: dict) -> None:
    _path(filename).write_text(json.dumps(data, indent=2))
