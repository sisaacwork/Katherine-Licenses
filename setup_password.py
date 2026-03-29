"""
Run this once to generate a bcrypt password hash for secrets.toml.

    python setup_password.py
"""
import bcrypt
import getpass

password = getpass.getpass("Enter app password: ").encode()
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()

print("\nAdd this to .streamlit/secrets.toml:\n")
print(f'[auth]')
print(f'password_hash = "{hashed}"')
