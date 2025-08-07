import re

def validate_username(username: str):
    if not re.match(r"^[a-zA-Z0-9_.-]{4,20}$", username):
        raise ValueError("Username must be 4-20 chars (letters, digits, _.-)")

def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    # Add more password rules as needed
