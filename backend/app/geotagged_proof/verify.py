def build_verification_result(
    activity_id,
    location_verified,
    timestamp_verified,
    visual_match_confidence,
    photo_verified,
    reason
):
    """
    Build the final geotagged visual proof verification result.

    The visual verification values will eventually come
    from the AI verification module.
    """

    # Calculate overall confidence from the three
    # verification signals.
    location_score = 1.0 if location_verified else 0.0
    timestamp_score = 1.0 if timestamp_verified else 0.0

    overall_confidence = (
        0.40 * visual_match_confidence
        + 0.30 * location_score
        + 0.30 * timestamp_score
    )

    if (
        photo_verified
        and location_verified
        and timestamp_verified
    ):
        status = "Verified"

    elif (
        photo_verified
        or location_verified
        or timestamp_verified
    ):
        status = "Partially Verified"

    else:
        status = "Not Verified"

    return {
        "activity_id": activity_id,
        "photo_verified": photo_verified,
        "location_verified": location_verified,
        "timestamp_verified": timestamp_verified,
        "visual_match_confidence": round(
            visual_match_confidence,
            2
        ),
        "overall_confidence": round(
            overall_confidence,
            2
        ),
        "status": status,
        "reason": reason
    }