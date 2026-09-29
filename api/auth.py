import base64

USERNAME = "admin"
PASSWORD = "password123"


def check_basic_auth(header):
    """Return True if the Authorization header has valid Basic credentials."""
    if not header or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        user, pwd = decoded.split(":", 1)
    except Exception:
        return False
    return user == USERNAME and pwd == PASSWORD