import uuid
import streamlit as st
from datetime import datetime

from utils.dates import illinois_dates, days_until, format_countdown
from utils.state import load, save
import utils.drive as drv

st.set_page_config(page_title="Illinois — IDFPR", page_icon="🇺🇸", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please log in from the Home page.")
    st.stop()

st.title("🇺🇸 Illinois — IDFPR (LSW)")
st.caption("Illinois Department of Financial and Professional Regulation")

il_start, il_deadline, today = illinois_dates()
il_cycle = f"{il_start.year}–{il_deadline.year}"

# ── Countdown ──────────────────────────────────────────────────────────────────

c1, c2, c3 = st.columns(3)
c1.metric("Renewal Deadline", format_countdown(days_until(il_deadline)), f"Nov 30, {il_deadline.year}")
c2.metric("Biennial Fee", "US $60")
c3.metric("Active Cycle", il_cycle, f"Started Dec 1, {il_start.year}")

st.info(
    "Renewal applications open approximately **60 days before November 30, 2027**. "
    "You are solely responsible for keeping your license active regardless of whether IDFPR sends a notice."
)

st.divider()

# ── State ──────────────────────────────────────────────────────────────────────

state = load("illinois.json")
cycle_state = state.setdefault(il_cycle, {"entries": [], "sexual_harassment_employer": False})
entries: list[dict] = cycle_state.setdefault("entries", [])
sh_employer: bool = cycle_state.get("sexual_harassment_employer", False)

# ── CEU Requirements ───────────────────────────────────────────────────────────

SPECIALTY_REQS = {
    "Ethics": 3.0,
    "Cultural Competency": 3.0,
    "Implicit Bias Awareness": 1.0,
}
TOTAL_REQUIRED = 30.0

CATEGORIES = [
    "Ethics",
    "Cultural Competency",
    "Implicit Bias Awareness",
    "Sexual Harassment Prevention",
    "Mandated Reporter Training",
    "General / Other",
]

category_hours: dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
for e in entries:
    cat = e.get("category", "General / Other")
    category_hours[cat] = category_hours.get(cat, 0.0) + e.get("hours", 0.0)

total_hours = sum(category_hours.values())

# ── Progress Display ───────────────────────────────────────────────────────────

st.subheader(f"CEU Progress — {il_cycle} Cycle")
st.caption("All 30 hours must be obtained between Dec 1, 2025 and Nov 30, 2027.")

st.markdown(f"### {total_hours:.1f} / {TOTAL_REQUIRED:.0f} hours")
st.progress(min(total_hours / TOTAL_REQUIRED, 1.0))

col_spec, col_other = st.columns(2, gap="large")

with col_spec:
    st.markdown("**Specialty Requirements**")

    for cat, req in SPECIALTY_REQS.items():
        hrs = category_hours[cat]
        met = hrs >= req
        icon = "✅" if met else ("🟡" if hrs > 0 else "🔴")
        st.markdown(f"{icon} **{cat}**: {hrs:.1f} / {req:.1f} hrs")
        if not met:
            st.progress(hrs / req)

with col_other:
    st.markdown("**Other Requirements**")

    # Sexual Harassment Prevention
    sh_hrs = category_hours.get("Sexual Harassment Prevention", 0.0)
    sh_met = sh_employer or sh_hrs >= 1.0
    sh_icon = "✅" if sh_met else "🔴"
    st.markdown(f"{sh_icon} **Sexual Harassment Prevention**")

    new_sh_employer = st.checkbox(
        "Completed via employer training (no CEU hours required)",
        value=sh_employer,
        key="il_sh_employer",
        help="Employer training counts if taken within this licensure cycle.",
    )
    if not new_sh_employer:
        st.caption(f"IDFPR-approved course: {sh_hrs:.1f} / 1.0 hrs logged")
    if new_sh_employer != sh_employer:
        cycle_state["sexual_harassment_employer"] = new_sh_employer
        state[il_cycle] = cycle_state
        save("illinois.json", state)
        st.toast("Saved!", icon="✅")
        sh_employer = new_sh_employer
        sh_met = sh_employer or sh_hrs >= 1.0

    st.divider()

    mr_hrs = category_hours.get("Mandated Reporter Training", 0.0)
    mr_icon = "✅" if mr_hrs > 0 else "ℹ️"
    st.markdown(
        f"{mr_icon} **Mandated Reporter Training** (if applicable): {mr_hrs:.1f} hrs\n\n"
        "<small>Required every 3 years for mandated reporters. "
        "Can count toward 30-hr total if from IDFPR-approved sponsor.</small>",
        unsafe_allow_html=True,
    )

# Remaining summary
st.divider()
if total_hours >= TOTAL_REQUIRED and sh_met and all(
    category_hours[c] >= r for c, r in SPECIALTY_REQS.items()
):
    st.success("🎉 All CEU requirements met for the 2025–2027 cycle!")
else:
    needs = []
    for cat, req in SPECIALTY_REQS.items():
        rem = req - category_hours[cat]
        if rem > 0:
            needs.append(f"**{rem:.1f} more hrs** in {cat}")
    if not sh_met:
        needs.append("**Sexual Harassment Prevention** (employer training OR ≥1 hr from IDFPR sponsor)")
    total_rem = max(0.0, TOTAL_REQUIRED - total_hours)
    if total_rem > 0:
        needs.append(f"**{total_rem:.1f} total hours** remaining")
    if needs:
        st.warning("Still needed:\n- " + "\n- ".join(needs))

st.divider()

# ── Upload Form ────────────────────────────────────────────────────────────────

st.subheader("Upload CEU Certificate")

service = drv.get_service()
drive_ok = service is not None

if not drive_ok:
    st.info(
        "Google Drive not configured — file storage is disabled. "
        "CEU entries will still be tracked locally. "
        "See `.streamlit/secrets.toml.example` to enable."
    )

with st.form("il_upload_form", clear_on_submit=True):
    fc1, fc2 = st.columns(2)
    category = fc1.selectbox("CEU Category", CATEGORIES)
    hours = fc2.number_input("Hours", min_value=0.5, max_value=50.0, step=0.5, value=1.0)

    fd1, fd2 = st.columns(2)
    date_attended = fd1.date_input(
        "Date Attended",
        value=today,
        min_value=il_start,
        max_value=il_deadline,
    )
    remote = fd2.checkbox(
        "Remote / online course",
        help="IDFPR requires that remote CEUs include a post-course examination.",
    )

    notes = st.text_input("Course title / provider / notes (optional)")
    cert_file = st.file_uploader("Certificate PDF", type=["pdf"])

    submitted = st.form_submit_button("➕ Add CEU Entry", use_container_width=True)

if submitted:
    if not cert_file:
        st.error("Please attach a certificate PDF.")
    else:
        drive_link = None
        drive_file_id = None

        if drive_ok:
            with st.spinner("Uploading to Google Drive…"):
                folder_id = drv.get_upload_folder(
                    service, "Illinois", il_cycle, "CEU Certificates"
                )
                result = drv.upload_file(
                    service, cert_file.getvalue(), cert_file.name, "application/pdf", folder_id
                )
                drive_link = result["webViewLink"]
                drive_file_id = result["id"]

        entry = {
            "id": str(uuid.uuid4())[:8],
            "filename": cert_file.name,
            "category": category,
            "hours": float(hours),
            "date_attended": str(date_attended),
            "remote": remote,
            "notes": notes.strip(),
            "uploaded_at": datetime.now().isoformat()[:16],
            "drive_file_id": drive_file_id,
            "drive_link": drive_link,
        }
        cycle_state["entries"].append(entry)
        state[il_cycle] = cycle_state
        save("illinois.json", state)

        msg = f"Added **{hours:.1f} hr(s)** — {category}"
        if drive_link:
            msg += f" — [View in Drive]({drive_link})"
        st.success(msg)
        st.rerun()

st.divider()

# ── CEU Log ────────────────────────────────────────────────────────────────────

st.subheader(f"CEU Log — {il_cycle}")

if not entries:
    st.caption("No entries yet. Upload your first certificate above.")
else:
    # Header row
    h1, h2, h3, h4, h5 = st.columns([4, 2, 1.5, 1.5, 0.7])
    h1.markdown("**Certificate**")
    h2.markdown("**Category**")
    h3.markdown("**Hrs**")
    h4.markdown("**Date**")
    h5.markdown("**Del**")

    st.divider()

    for entry in sorted(entries, key=lambda e: e.get("date_attended", ""), reverse=True):
        c1, c2, c3, c4, c5 = st.columns([4, 2, 1.5, 1.5, 0.7])

        # Filename (linked if Drive link available)
        name = entry.get("filename", "—")
        link = entry.get("drive_link")
        label = f"[{name}]({link})" if link else name
        if entry.get("notes"):
            label += f" · *{entry['notes']}*"
        if entry.get("remote"):
            label += " 🌐"
        c1.markdown(label)

        c2.markdown(entry.get("category", "—"))
        c3.markdown(f"{entry.get('hours', 0):.1f}")
        c4.markdown(entry.get("date_attended", "—"))

        if c5.button("🗑", key=f"del_{entry['id']}", help="Remove this entry"):
            cycle_state["entries"] = [e for e in entries if e["id"] != entry["id"]]
            state[il_cycle] = cycle_state
            save("illinois.json", state)
            st.toast("Entry removed.", icon="🗑️")
            st.rerun()

    st.caption(f"{len(entries)} entries · {total_hours:.1f} hrs total")
