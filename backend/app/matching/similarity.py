from difflib import SequenceMatcher


def text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two activity descriptions.

    Returns a score between 0 and 1.
    1.0 = identical
    0.0 = completely different
    """

    if not text1 or not text2:
        return 0.0

    text1 = text1.lower().strip()
    text2 = text2.lower().strip()

    return SequenceMatcher(None, text1, text2).ratio()