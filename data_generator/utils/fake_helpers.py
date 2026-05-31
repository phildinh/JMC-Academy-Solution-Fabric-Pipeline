import random


def apply_email_casing(email: str, rng: random.Random) -> str:
    """Apply random uppercase or mixed case to ~30% of emails to simulate casing mess."""
    r = rng.random()
    if r < 0.15:
        return email.upper()
    elif r < 0.30:
        local, domain = email.split("@", 1)
        return local.capitalize() + "@" + domain.capitalize()
    return email
