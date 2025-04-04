import re


def clean_text(text: str) -> str:
    """Cleans the text by removing extra spaces and converting to lowercase."""
    return re.sub(r"\s+", " ", text).strip().lower()
