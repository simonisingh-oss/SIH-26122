from pathlib import Path
import shutil


UPLOAD_DIR = Path("data/visual_proofs")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_uploaded_photo(
    uploaded_file,
    activity_id
):
    """
    Save an uploaded site photo.

    The photo is stored inside:
    data/visual_proofs/<activity_id>/

    Returns the saved file path.
    """

    activity_directory = UPLOAD_DIR / activity_id

    activity_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = activity_directory / uploaded_file.filename

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            uploaded_file.file,
            buffer
        )

    return str(file_path)