from ..database import get_connection
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from .storage import save_uploaded_photo
from .metadata import extract_metadata
from .location import is_point_inside_boundary


router = APIRouter(
    prefix="/visual-proof",
    tags=["Geotagged Visual Proof"]
)


@router.post("/upload")
async def upload_visual_proof(
    activity_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a site photo for a reported activity.

    The endpoint:
    1. Receives activity ID and photo.
    2. Saves the photo.
    3. Extracts GPS and timestamp metadata.
    4. Validates GPS against the site boundary.
    """

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type"
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    file_path = save_uploaded_photo(
        file,
        activity_id
    )

    metadata = extract_metadata(
        file_path
    )

    location_verified = is_point_inside_boundary(
        metadata["latitude"],
        metadata["longitude"]
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO visual_proofs (
            activity_id,
            photo_path,
            latitude,
            longitude,
            photo_timestamp,
            location_verified
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        activity_id,
        file_path,
        metadata["latitude"],
        metadata["longitude"],
        metadata["timestamp"],
        int(location_verified)
    ))

    connection.commit()
    connection.close()

    return {
        "activity_id": activity_id,
        "photo_path": file_path,
        "latitude": metadata["latitude"],
        "longitude": metadata["longitude"],
        "timestamp": metadata["timestamp"],
        "location_verified": location_verified,
        "metadata_available": (
            metadata["latitude"] is not None
            or metadata["longitude"] is not None
            or metadata["timestamp"] is not None
        )
    }
@router.post("/verify")
def verify_visual_proof(
    activity_id: str = Form(...),
    photo_verified: bool = Form(...),
    timestamp_verified: bool = Form(...),
    visual_match_confidence: float = Form(...),
    reason: str = Form(...)
):
    """
    Combine backend location verification with
    the AI visual verification result.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Get the latest uploaded proof for this activity
    cursor.execute("""
        SELECT
            location_verified,
            photo_path,
            latitude,
            longitude,
            photo_timestamp
        FROM visual_proofs
        WHERE activity_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (activity_id,))

    proof = cursor.fetchone()

    if not proof:
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="No uploaded visual proof found for this activity."
        )

    location_verified = bool(proof[0])

    # Build final verification result
    from .verify import build_verification_result

    result = build_verification_result(
        activity_id=activity_id,
        location_verified=location_verified,
        timestamp_verified=timestamp_verified,
        visual_match_confidence=visual_match_confidence,
        photo_verified=photo_verified,
        reason=reason
    )

    # Save AI verification result
    cursor.execute("""
        UPDATE visual_proofs
        SET
            photo_verified = ?,
            timestamp_verified = ?,
            visual_match_confidence = ?,
            overall_confidence = ?,
            verification_status = ?,
            verification_reason = ?
        WHERE activity_id = ?
        AND id = (
            SELECT id
            FROM visual_proofs
            WHERE activity_id = ?
            ORDER BY id DESC
            LIMIT 1
        )
    """, (
        int(result["photo_verified"]),
        int(result["timestamp_verified"]),
        result["visual_match_confidence"],
        result["overall_confidence"],
        result["status"],
        result["reason"],
        activity_id,
        activity_id
    ))

    connection.commit()
    connection.close()

    return result