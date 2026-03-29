import bcrypt
import streamlit as st

from utils.dates import ontario_dates, illinois_dates, days_until, format_countdown
from utils.state import load

st.set_page_config(
    page_title="SW License Tracker",
    page_icon="📋",
    layout="wide",
)


# ── Authentication ─────────────────────────────────────────────────────────────

def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("📋 SW License Tracker")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            stored = st.secrets["auth"]["password_hash"].encode()
            if bcrypt.checkpw(password.encode(), stored):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        except KeyError:
            st.warning(
                "Auth not configured yet. "
                "Run `python setup_password.py` and add the hash to `.streamlit/secrets.toml`."
            )
    return False


if not check_password():
    st.stop()


# ── Dashboard ──────────────────────────────────────────────────────────────────

st.title("📋 SW License Tracker")
st.caption("Ontario (OCSWSSW) · Illinois (IDFPR/LSW)")

on_opens, on_deadline, today = ontario_dates()
il_start, il_deadline, _ = illinois_dates()
il_cycle = f"{il_start.year}–{il_deadline.year}"

# Ontario quick stats
on_state = load("ontario.json")
on_year = str(today.year)
on_steps = on_state.get(on_year, {}).get("steps", {})
on_steps_done = sum(1 for v in on_steps.values() if v)

# Illinois quick stats
il_state = load("illinois.json")
il_cycle_state = il_state.get(il_cycle, {})
il_entries = il_cycle_state.get("entries", [])
il_total_hrs = sum(e.get("hours", 0) for e in il_entries)
il_sh_employer = il_cycle_state.get("sexual_harassment_employer", False)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("🇨🇦 Ontario — OCSWSSW")

    days_open = days_until(on_opens)
    days_due = days_until(on_deadline)

    if today < on_opens:
        st.metric("Renewal Opens", format_countdown(days_open), f"Nov 1, {on_opens.year}")
    else:
        st.metric("Renewal Deadline", format_countdown(days_due), "Renewal is OPEN")

    c1, c2 = st.columns(2)
    c1.metric("Annual Fee", "CA $400")
    c2.metric("CCP Steps Done", f"{on_steps_done} / 4")

    st.progress(on_steps_done / 4)

    if on_steps_done == 4:
        st.success("All CCP steps complete for {on_year}!")
    else:
        remaining = 4 - on_steps_done
        st.warning(f"{remaining} CCP step{'s' if remaining != 1 else ''} still to complete")

with col2:
    st.subheader("🇺🇸 Illinois — IDFPR (LSW)")

    days_il = days_until(il_deadline)
    st.metric("Renewal Deadline", format_countdown(days_il), f"Nov 30, {il_deadline.year}")

    c1, c2 = st.columns(2)
    c1.metric("Biennial Fee", "US $60")
    c2.metric("CEUs Logged", f"{il_total_hrs:.1f} / 30 hrs")

    st.progress(min(il_total_hrs / 30.0, 1.0))

    if il_total_hrs >= 30:
        st.success("30-hour CEU requirement met!")
    else:
        st.info(f"{30 - il_total_hrs:.1f} hours remaining — cycle {il_cycle}")

st.divider()
st.caption("Use the sidebar to manage each jurisdiction.")
