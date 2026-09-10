def confidence_level(score: float) -> str:
    """
    Convert a matching score into a human-readable confidence level.
    """

    if score >= 0.70:
        return "High"

    if score >= 0.55:
        return "Medium"

    if score >= 0.40:
        return "Low"

    return "Very Low"