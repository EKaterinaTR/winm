"""Validation helpers: normalize name for uniqueness (case and whitespace insensitive)."""


def normalize_name(name: str) -> str:
    """Normalize for uniqueness: strip leading/trailing whitespace, lowercase."""
    return name.strip().lower()
