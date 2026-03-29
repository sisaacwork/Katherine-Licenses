# Katherine's SW License Tracker

A personal Streamlit app for tracking social work licensure requirements in two jurisdictions.

| Jurisdiction | Body | Renewal | Cost |
|---|---|---|---|
| Ontario | OCSWSSW | Nov 1 – Dec 31 (annual) | CA $400 |
| Illinois | IDFPR (LSW) | By Nov 30 of odd years | US $60 / 2 yrs |

## Features

- **Countdown timers** to renewal open and deadline dates
- **Ontario CCP checklist** — 4-step Continuing Competency Program (Steps 1–4)
- **Illinois CEU tracker** — 30-hour log with specialty category minimums and progress bars
- **Google Drive upload portal** — certificates and CCP documents saved to organized Drive folders
- **State persisted to Drive** — survives Streamlit Cloud restarts

## Local setup

```bash
pip install -r requirements.txt

# Generate a bcrypt password hash
python setup_password.py

# Configure secrets (see below), then:
streamlit run app.py
```

## Secrets configuration

Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and fill in:

1. `[auth] password_hash` — output of `setup_password.py`
2. `[google_service_account]` — paste your service account JSON key fields
3. `[drive] root_folder_id` — ID of the Drive folder shared with the service account

### Google Drive setup (one-time)

1. [Google Cloud Console](https://console.cloud.google.com/) → New project → **Enable Drive API**
2. **IAM & Admin → Service Accounts** → Create → download JSON key
3. In Google Drive, create a folder (e.g. `SW Licenses`) → Share it with the service account email
4. Copy the folder ID from the Drive URL: `drive.google.com/drive/folders/`**`THIS_PART`**

## Streamlit Cloud deployment

1. Push this repo to GitHub (keep `secrets.toml` out — it's gitignored)
2. [share.streamlit.io](https://share.streamlit.io) → New app → select this repo, `app.py`
3. **Advanced settings → Secrets** → paste the full contents of your `secrets.toml`

## Drive folder structure (auto-created)

```
[Root Folder]/
├── _state/
│   ├── ontario.json        ← CCP checklist state
│   └── illinois.json       ← CEU log
├── Ontario/
│   └── 2026/
│       ├── CCP Documents/
│       └── CEU Certificates/
└── Illinois/
    └── 2025–2027/
        └── CEU Certificates/
```
