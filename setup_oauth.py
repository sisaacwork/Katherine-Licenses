"""Run this script ONCE locally to generate an OAuth 2.0 refresh token.

Steps:
  1. Go to https://console.cloud.google.com/
  2. Select your project → APIs & Services → Credentials
  3. Create an OAuth 2.0 Client ID → Desktop app → Download JSON
     (OR just paste the client_id and client_secret when prompted below)
  4. Run:  python setup_oauth.py
  5. A browser tab will open — log in as Katie and click Allow
  6. Copy the three values printed at the end into .streamlit/secrets.toml

The refresh token does not expire unless Katie revokes access, so you only
need to do this once (or again if you ever revoke & re-grant access).
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

print("=" * 60)
print("  Katherine Licenses — Google Drive OAuth Setup")
print("=" * 60)
print()
print("Paste the values from your OAuth 2.0 Client ID (Desktop app).")
print("Find them at: console.cloud.google.com → APIs & Services → Credentials")
print()

client_id = input("client_id:     ").strip()
client_secret = input("client_secret: ").strip()

client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print()
print("Opening browser for Google sign-in…")
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

print()
print("=" * 60)
print("  SUCCESS — add these to .streamlit/secrets.toml")
print("=" * 60)
print()
print("[google_oauth]")
print(f'client_id     = "{creds.client_id}"')
print(f'client_secret = "{creds.client_secret}"')
print(f'refresh_token = "{creds.refresh_token}"')
print()
print("Then remove (or leave) the [google_service_account] block —")
print("it is no longer used.")
