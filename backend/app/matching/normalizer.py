import re


def normalize_text(text: str) -> str:
    """
    Cleans activity descriptions so that
    similar activities can be compared more reliably.
    """

    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace special characters with spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text