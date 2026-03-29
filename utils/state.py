"""State persistence: Drive when configured (required for Streamlit Cloud), local fallback.

Session cache avoids repeated Drive API calls within a single user session.
"""
import json
import streamlit as st
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"


def _local_path(filename: str) -> Path:
    try:
        _DATA_DIR.mkdir(exist_ok=True)
    except Exception:
        pass
    return _DATA_DIR / filename


def load(filename: str) -> dict:
    """Load state dict. Checks session cache first, then Drive (or local fallback)."""
    cache_key = f"_state_{filename}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    import utils.drive as drv
    service = drv.get_service()
    if service and drv.is_configured():
        data = drv.read_json(service, filename)
    else:
        p = _local_path(filename)
        data = json.loads(p.read_text()) if p.exists() else {}

    st.session_state[cache_key] = data
    return data


def save(filename: str, data: dict) -> None:
    """Persist state to Drive (or local) and update session cache."""
    st.session_state[f"_state_{filename}"] = data

    import utils.drive as drv
    service = drv.get_service()
    if service and drv.is_configured():
        drv.write_json(service, filename, data)
    else:
        try:
            _local_path(filename).write_text(json.dumps(data, indent=2))
        except Exception:
            pass
