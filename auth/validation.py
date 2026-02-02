import re


def is_valid_email(email: str) -> bool:
    """Basic email format check — must contain @ with a . in the domain part."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def password_strength(password: str) -> str:
    """Return 'weak', 'medium', or 'strong' based on length and character variety."""
    categories = 0
    if re.search(r"[a-z]", password):
        categories += 1
    if re.search(r"[A-Z]", password):
        categories += 1
    if re.search(r"[0-9]", password):
        categories += 1
    if re.search(r"[^a-zA-Z0-9]", password):
        categories += 1

    if len(password) >= 12 and categories >= 3:
        return "strong"
    if len(password) >= 8 and categories >= 2:
        return "medium"
    return "weak"
