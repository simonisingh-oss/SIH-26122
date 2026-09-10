# Temporary demo boundary.
# Replace these coordinates with the actual project/site boundary later.

SITE_BOUNDARY = [
    [28.6000, 77.2000],
    [28.6000, 77.2100],
    [28.6100, 77.2100],
    [28.6100, 77.2000]
]


def is_point_inside_boundary(
    latitude,
    longitude,
    boundary=SITE_BOUNDARY
):
    """
    Check whether a GPS point is inside the site boundary.

    Coordinates are in:
    [latitude, longitude]

    Returns:
        True  -> point is inside boundary
        False -> point is outside boundary
    """

    if latitude is None or longitude is None:
        return False

    if not boundary or len(boundary) < 3:
        return False

    inside = False

    j = len(boundary) - 1

    for i in range(len(boundary)):

        lat_i, lon_i = boundary[i]
        lat_j, lon_j = boundary[j]

        intersects = (
            ((lat_i > latitude) != (lat_j > latitude))
            and
            (
                longitude
                < (lon_j - lon_i)
                * (latitude - lat_i)
                / (lat_j - lat_i)
                + lon_i
            )
        )

        if intersects:
            inside = not inside

        j = i

    return inside