from datetime import datetime, time


def parse_timestamp(value):
    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y:%m:%d %H:%M:%S",   # EXIF format
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def verify_photo_timestamp(
    photo_timestamp,
    reported_start=None,
    reported_end=None
):
    """
    Verify that the photo timestamp falls within
    the reported activity period.
    """

    photo_dt = parse_timestamp(photo_timestamp)

    if not photo_dt:
        return False

    start_dt = parse_timestamp(reported_start)

    if not start_dt:
        return False

    end_dt = parse_timestamp(reported_end)

    if not end_dt:
        end_dt = start_dt

    # If only a date was supplied for the end,
    # consider the entire day valid.
    if len(str(reported_end).strip()) == 10:
        end_dt = datetime.combine(
            end_dt.date(),
            time.max
        )

    return start_dt <= photo_dt <= end_dt