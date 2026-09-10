from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def _convert_to_degrees(value):
    """
    Convert GPS coordinates from EXIF format
    (degrees, minutes, seconds) to decimal degrees.
    """

    degrees = float(value[0])
    minutes = float(value[1])
    seconds = float(value[2])

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def extract_metadata(image_path):
    """
    Extract GPS coordinates and timestamp from an image.

    Returns:
        {
            "latitude": ...,
            "longitude": ...,
            "timestamp": ...
        }
    """

    result = {
        "latitude": None,
        "longitude": None,
        "timestamp": None
    }

    try:
        image = Image.open(image_path)
        exif_data = image.getexif()

        if not exif_data:
            return result

        # Convert EXIF tag IDs into readable names
        exif = {}

        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value

        # Extract timestamp
        result["timestamp"] = (
            exif.get("DateTimeOriginal")
            or exif.get("DateTime")
        )

        # Extract GPS information
        gps_info = exif.get("GPSInfo")

        if not gps_info:
            return result

        gps = {}

        for key, value in gps_info.items():
            tag = GPSTAGS.get(key, key)
            gps[tag] = value

        latitude = gps.get("GPSLatitude")
        latitude_ref = gps.get("GPSLatitudeRef")

        longitude = gps.get("GPSLongitude")
        longitude_ref = gps.get("GPSLongitudeRef")

        if latitude and longitude:

            latitude = _convert_to_degrees(latitude)
            longitude = _convert_to_degrees(longitude)

            if latitude_ref == "S":
                latitude = -latitude

            if longitude_ref == "W":
                longitude = -longitude

            result["latitude"] = latitude
            result["longitude"] = longitude

        return result

    except Exception as error:

        print(f"Metadata extraction error: {error}")

        return result