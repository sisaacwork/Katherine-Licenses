import streamlit as st

from utils.dates import ontario_dates, days_until, format_countdown
from utils.state import load, save
import utils.drive as drv

st.set_page_config(page_title="Ontario — OCSWSSW", page_icon="🇨🇦", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please log in from the Home page.")
    st.stop()

st.title("🇨🇦 Ontario — OCSWSSW")
st.caption(
    "Ontario College of Social Workers and Social Service Workers · "
    "[📄 CCP Self-Assessment Tool & PDP (2026)](https://www.ocswssw.org/wp-content/uploads/OCSWSSW-CCP-Assess-Tool-2026-English.pdf)"
)

on_opens, on_deadline, today = ontario_dates()
current_year = str(today.year)

# ── Countdown ──────────────────────────────────────────────────────────────────

c1, c2, c3 = st.columns(3)
days_open = days_until(on_opens)
days_due = days_until(on_deadline)

if today < on_opens:
    c1.metric("Renewal Opens In", format_countdown(days_open), f"Nov 1, {on_opens.year}")
    c2.metric("Renewal Deadline", f"Dec 31, {on_deadline.year}", "Not yet open")
else:
    c1.metric("Renewal", "OPEN NOW", f"Opened Nov 1, {on_opens.year}")
    c2.metric("Deadline In", format_countdown(days_due), f"Dec 31, {on_deadline.year}")

c3.metric("Annual Renewal Fee", "CA $400")

st.divider()

# ── CCP Checklist ──────────────────────────────────────────────────────────────

st.subheader(f"Continuing Competency Program — {current_year}")
st.caption(
    "Complete all four steps annually. Retain the full CCP portfolio for a minimum of **10 years**."
)

STEPS = [
    (
        "step1",
        "Step 1 — Review Code of Ethics & Standards of Practice",
        "Review the *Code of Ethics and Standards of Practice* (3rd Ed., 2023) and any other "
        "documents posted for this CCP year. Complete the Standards of Practice Checklist.",
    ),
    (
        "step2",
        "Step 2 — Complete the Self-Assessment Tool (SAT)",
        "Identify your strengths, gather peer/supervisor feedback (if applicable), identify "
        "learning needs and interests, and develop learning goals.",
    ),
    (
        "step3",
        "Step 3 — Complete the Professional Development Plan (PDP)",
        "Transfer learning goals to the PDP. Complete each learning activity, record completion, "
        "and retain all documentation (receipts, certificates, slides, articles, etc.).",
    ),
    (
        "step4",
        "Step 4 — Submit Declaration of Participation",
        "Complete the Declaration of Participation as part of your Annual Renewal of Registration "
        "online. Retain all CCP portfolio documents.",
    ),
]

# Load and display
state = load("ontario.json")
year_state = state.get(current_year, {"steps": {s[0]: False for s in STEPS}})
steps = year_state.setdefault("steps", {s[0]: False for s in STEPS})

changed = False
for key, title, desc in STEPS:
    val = st.checkbox(title, value=steps.get(key, False), key=f"on_{key}_{current_year}")
    st.caption(f"\u00a0\u00a0\u00a0\u00a0{desc}")
    if val != steps.get(key, False):
        steps[key] = val
        changed = True

if changed:
    year_state["steps"] = steps
    state[current_year] = year_state
    save("ontario.json", state)
    st.toast("Progress saved!", icon="✅")

done = sum(1 for v in steps.values() if v)
st.progress(done / 4, text=f"{done} of 4 steps complete")

st.divider()

# ── Document Uploads ───────────────────────────────────────────────────────────

st.subheader("Documents")

service = drv.get_service()
drive_ok = service is not None

if not drive_ok:
    st.info(
        "Google Drive not configured — uploads are disabled. "
        "See `.streamlit/secrets.toml.example` to enable."
    )

tab_ccp, tab_ceu = st.tabs(["📄 CCP Portfolio Documents", "📜 CEU Certificates"])

with tab_ccp:
    st.markdown(
        "Upload your completed **Standards of Practice Checklist**, **Self-Assessment Tool (SAT)**, "
        "and **Professional Development Plan (PDP)** PDFs for this year's portfolio."
    )
    uploaded = st.file_uploader(
        "Select CCP document (PDF)", type=["pdf"], key="on_ccp_file"
    )
    if uploaded and drive_ok:
        if st.button("Upload to Google Drive", key="on_ccp_upload_btn"):
            with st.spinner("Uploading…"):
                folder_id = drv.get_upload_folder(service, "Ontario", current_year, "CCP Documents")
                result = drv.upload_file(
                    service, uploaded.getvalue(), uploaded.name, "application/pdf", folder_id
                )
            st.success(f"Uploaded — [Open in Drive]({result['webViewLink']})")

    if drive_ok:
        with st.expander("View uploaded CCP documents"):
            folder_id = drv.get_upload_folder(service, "Ontario", current_year, "CCP Documents")
            files = drv.list_files(service, folder_id)
            if files:
                for f in files:
                    st.markdown(f"- [{f['name']}]({f['webViewLink']}) · {f['createdTime'][:10]}")
            else:
                st.caption("No documents uploaded yet.")

with tab_ceu:
    st.markdown(
        "Upload CEU completion certificates for any learning activities completed as part of your PDP."
    )
    uploaded = st.file_uploader(
        "Select CEU certificate (PDF)", type=["pdf"], key="on_ceu_file"
    )
    if uploaded and drive_ok:
        if st.button("Upload to Google Drive", key="on_ceu_upload_btn"):
            with st.spinner("Uploading…"):
                folder_id = drv.get_upload_folder(service, "Ontario", current_year, "CEU Certificates")
                result = drv.upload_file(
                    service, uploaded.getvalue(), uploaded.name, "application/pdf", folder_id
                )
            st.success(f"Uploaded — [Open in Drive]({result['webViewLink']})")

    if drive_ok:
        with st.expander("View uploaded CEU certificates"):
            folder_id = drv.get_upload_folder(service, "Ontario", current_year, "CEU Certificates")
            files = drv.list_files(service, folder_id)
            if files:
                for f in files:
                    st.markdown(f"- [{f['name']}]({f['webViewLink']}) · {f['createdTime'][:10]}")
            else:
                st.caption("No certificates uploaded yet.")
