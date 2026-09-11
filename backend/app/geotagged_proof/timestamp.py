from datetime import datetime


def verify_photo_timestamp(
    photo_timestamp,
    reported_start=None,
    reported_end=None
):
    """
    Check whether the photo timestamp falls within
    the reported activity time period.

    Returns:
        True  -> timestamp is within the reported period
        False -> timestamp is missing or outside the period
    """

    if not photo_timestamp:
        return False

    try:
        # EXIF timestamp format:
        # YYYY:MM:DD HH:MM:SS
        photo_time = datetime.strptime(
            photo_timestamp,
            "%Y:%m:%d %H:%M:%S"
        )

        if reported_start:
            reported_start = datetime.fromisoformat(
                str(reported_start).replace("Z", "")
            )

            if photo_time < reported_start:
                return False

        if reported_end:
            reported_end = datetime.fromisoformat(
                str(reported_end).replace("Z", "")
            )

            if photo_time > reported_end:
                return False

        return True

    except (ValueError, TypeError):
        return False