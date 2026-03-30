"""Credential Vault — store, preview, and share important credential PDFs."""
import base64
import uuid
from datetime import datetime

import streamlit as st

from utils.state import load, save
import utils.drive as drv

st.set_page_config(page_title="Credential Vault", page_icon="📁", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please log in from the Home page.")
    st.stop()

st.title("📁 Credential Vault")
st.caption(
    "Store, preview, and instantly share your licenses, diplomas, and credentials. "
    "Use the **Replace** button whenever a document is renewed or updated."
)

# ── Drive ─────────────────────────────────────────────────────────────────────

service = drv.get_service()
drive_ok = service is not None

if not drive_ok:
    st.info(
        "Google Drive not configured — file uploads are disabled. "
        "See `.streamlit/secrets.toml.example` to enable."
    )

# ── State ─────────────────────────────────────────────────────────────────────

state = load("documents.json")
docs: dict = state.setdefault("docs", {})                    # slot_key → file_info dict
custom_labels: dict = state.setdefault("custom_labels", {})  # slot_key → {label, icon}

# ── Pre-defined credential slots ──────────────────────────────────────────────

PREDEFINED = [
    ("ontario_license",  "🪪", "Ontario RSW License"),
    ("illinois_license", "🪪", "Illinois LSW License"),
    ("ediploma",         "🎓", "eDiploma / Degree Certificate"),
    ("transcripts",      "📋", "Official Transcripts"),
    ("resume",           "📄", "Current Résumé / CV"),
]

# ── Card renderer ─────────────────────────────────────────────────────────────

def render_card(slot_key: str, icon: str, label: str) -> None:
    """Render one credential card with upload, replace, and inline PDF preview."""
    info: dict | None = docs.get(slot_key)
    replacing: bool = st.session_state.get(f"replacing_{slot_key}", False)

    with st.container(border=True):
        title_col, btn_col = st.columns([5, 1])

        # ── Header ──
        with title_col:
            st.markdown(f"#### {icon} {label}")
            if info:
                st.caption(
                    f"📎 **{info['filename']}** · uploaded {info['uploaded_at'][:10]}"
                )
                if info.get("drive_link"):
                    st.markdown(f"[🔗 Open in Google Drive ↗]({info['drive_link']})")
            else:
                st.caption("*No document uploaded yet.*")

        # ── Replace button (only when a file already exists) ──
        with btn_col:
            st.write("")  # nudge button down to align with title
            if info and not replacing:
                if st.button(
                    "🔄 Replace",
                    key=f"replace_btn_{slot_key}",
                    use_container_width=True,
                    help="Upload a newer version of this document",
                ):
                    st.session_state[f"replacing_{slot_key}"] = True
                    st.rerun()

        # ── Upload / Replace form ──
        if not info or replacing:
            verb = "Replace" if replacing else "Upload"
            new_file = st.file_uploader(
                f"{verb} PDF", type=["pdf"], key=f"uploader_{slot_key}"
            )

            if not drive_ok:
                st.caption("⚠️ Google Drive required for file storage.")

            if replacing:
                c_confirm, c_cancel = st.columns(2)
                confirmed = c_confirm.button(
                    "✅ Confirm Replace",
                    key=f"confirm_{slot_key}",
                    use_container_width=True,
                    disabled=not (new_file and drive_ok),
                )
                cancelled = c_cancel.button(
                    "✖ Cancel",
                    key=f"cancel_{slot_key}",
                    use_container_width=True,
                )
            else:
                confirmed = st.button(
                    "⬆ Upload to Drive",
                    key=f"confirm_{slot_key}",
                    disabled=not (new_file and drive_ok),
                )
                cancelled = False

            if confirmed and new_file:
                with st.spinner("Uploading to Google Drive…"):
                    folder_id = drv.get_upload_folder(service, "Credentials", "Files")
                    result = drv.upload_file(
                        service,
                        new_file.getvalue(),
                        new_file.name,
                        "application/pdf",
                        folder_id,
                    )
                docs[slot_key] = {
                    "filename": new_file.name,
                    "drive_file_id": result["id"],
                    "drive_link": result["webViewLink"],
                    "uploaded_at": datetime.now().isoformat()[:16],
                }
                state["docs"] = docs
                save("documents.json", state)
                # clear stale session flags & cached preview
                st.session_state.pop(f"replacing_{slot_key}", None)
                st.session_state.pop(f"preview_{slot_key}", None)
                st.toast(f"'{label}' saved!", icon="✅")
                st.rerun()

            if cancelled:
                st.session_state.pop(f"replacing_{slot_key}", None)
                st.rerun()

        # ── Inline PDF preview ──
        if info and info.get("drive_file_id") and drive_ok:
            with st.expander("👁 Preview PDF"):
                preview_key = f"preview_{slot_key}"

                if preview_key not in st.session_state:
                    if st.button("📄 Load Preview", key=f"load_preview_{slot_key}"):
                        try:
                            with st.spinner("Fetching PDF…"):
                                pdf_bytes = service.files().get_media(
                                    fileId=info["drive_file_id"]
                                ).execute()
                            st.session_state[preview_key] = pdf_bytes
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not load preview: {exc}")
                    st.caption(
                        "Preview downloads the PDF through your Drive connection. "
                        "For large files, use the Drive link above instead."
                    )
                else:
                    b64 = base64.b64encode(st.session_state[preview_key]).decode()
                    st.components.v1.html(
                        f'<iframe src="data:application/pdf;base64,{b64}" '
                        f'width="100%" height="700" '
                        f'style="border:none; border-radius:4px;"></iframe>',
                        height=710,
                    )
                    if st.button("✖ Close Preview", key=f"close_preview_{slot_key}"):
                        st.session_state.pop(preview_key)
                        st.rerun()

        elif info and not drive_ok:
            st.caption("ℹ️ Connect Google Drive to enable inline PDF preview.")


# ── Predefined slots ───────────────────────────────────────────────────────────

st.subheader("Credentials")

for slot_key, icon, label in PREDEFINED:
    render_card(slot_key, icon, label)
    st.write("")

st.divider()

# ── Custom document slots ──────────────────────────────────────────────────────

st.subheader("Additional Documents")
st.caption("Add slots for any other documents you want to keep on file.")

for slot_key, meta in list(custom_labels.items()):
    card_col, del_col = st.columns([11, 1])
    with card_col:
        render_card(slot_key, meta.get("icon", "📎"), meta["label"])
    with del_col:
        st.write("")
        st.write("")
        if st.button("🗑", key=f"del_custom_{slot_key}", help="Remove this document slot"):
            custom_labels.pop(slot_key, None)
            docs.pop(slot_key, None)
            state["custom_labels"] = custom_labels
            state["docs"] = docs
            save("documents.json", state)
            st.toast("Slot removed.", icon="🗑️")
            st.rerun()
    st.write("")

# ── Add custom slot ────────────────────────────────────────────────────────────

with st.expander("➕ Add a document slot"):
    with st.form("add_custom_form", clear_on_submit=True):
        new_label = st.text_input(
            "Document name",
            placeholder="e.g. NASW Membership Card, CPR Certificate…",
        )
        new_icon = st.selectbox(
            "Icon",
            ["📎", "📄", "📋", "🪪", "🎓", "🏅", "🔖", "📑", "🗂️", "🆔"],
        )
        add_ok = st.form_submit_button("Add Slot", use_container_width=True)

    if add_ok and new_label.strip():
        new_key = f"custom_{uuid.uuid4().hex[:8]}"
        custom_labels[new_key] = {"label": new_label.strip(), "icon": new_icon}
        state["custom_labels"] = custom_labels
        save("documents.json", state)
        st.toast(f'"{new_label.strip()}" slot added!', icon="✅")
        st.rerun()
    elif add_ok:
        st.warning("Please enter a document name.")
