"""Google Drive helpers using a service account."""
import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

_STATE_FOLDER = "_state"

SCOPES = ["https://www.googleapis.com/auth/drive"]


def is_configured() -> bool:
    try:
        _ = st.secrets["google_service_account"]
        _ = st.secrets["drive"]["root_folder_id"]
        return True
    except Exception:
        return False


@st.cache_resource
def get_service():
    """Return an authenticated Drive service, or None if credentials are missing."""
    if not is_configured():
        return None
    try:
        creds = service_account.Credentials.from_service_account_info(
            dict(st.secrets["google_service_account"]), scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception as exc:
        st.error(f"Drive auth error: {exc}")
        return None


def get_or_create_folder(service, name: str, parent_id: str = None) -> str:
    query = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
        " and trashed=false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    return service.files().create(body=body, fields="id").execute()["id"]


def get_folder_path(service, *parts: str) -> str:
    """Get (creating if needed) a nested folder path under the Drive root."""
    folder_id = st.secrets["drive"]["root_folder_id"]
    for part in parts:
        folder_id = get_or_create_folder(service, part, folder_id)
    return folder_id


def get_upload_folder(service, jurisdiction: str, subfolder: str, category: str = None) -> str:
    """Return (creating if needed) the folder for a given jurisdiction/subfolder/category."""
    root_id = st.secrets["drive"]["root_folder_id"]
    juris_id = get_or_create_folder(service, jurisdiction, root_id)
    sub_id = get_or_create_folder(service, subfolder, juris_id)
    if category:
        return get_or_create_folder(service, category, sub_id)
    return sub_id


def upload_file(service, file_bytes: bytes, filename: str, mime_type: str, folder_id: str) -> dict:
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
    body = {"name": filename, "parents": [folder_id]}
    return service.files().create(
        body=body, media_body=media, fields="id,name,webViewLink,createdTime"
    ).execute()


def list_files(service, folder_id: str) -> list[dict]:
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id,name,webViewLink,createdTime)",
        orderBy="createdTime desc",
    ).execute()
    return results.get("files", [])


# ── State JSON helpers (stored in Drive/_state/) ────────────────────────────

def _state_folder_id(service) -> str:
    root_id = st.secrets["drive"]["root_folder_id"]
    return get_or_create_folder(service, _STATE_FOLDER, root_id)


def read_json(service, filename: str) -> dict:
    """Read a JSON state file from Drive. Returns {} if not found."""
    try:
        folder_id = _state_folder_id(service)
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if not files:
            return {}
        content = service.files().get_media(fileId=files[0]["id"]).execute()
        return json.loads(content.decode("utf-8"))
    except Exception:
        return {}


def write_json(service, filename: str, data: dict) -> None:
    """Write/update a JSON state file in Drive."""
    content = json.dumps(data, indent=2).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json")
    folder_id = _state_folder_id(service)
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        service.files().update(fileId=files[0]["id"], media_body=media).execute()
    else:
        body = {"name": filename, "parents": [folder_id]}
        service.files().create(body=body, media_body=media).execute()
