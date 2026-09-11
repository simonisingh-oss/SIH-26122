from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..database import get_connection

from .storage import save_uploaded_photo
from .metadata import extract_metadata
from .location import is_point_inside_boundary
from .timestamp import verify_photo_timestamp


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
    5. Stores the visual proof information in the database.
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

    # Save uploaded photo
    file_path = save_uploaded_photo(
        file,
        activity_id
    )

    # Extract EXIF metadata
    metadata = extract_metadata(
        file_path
    )

    # Validate photo location against site boundary
    location_verified = is_point_inside_boundary(
        metadata["latitude"],
        metadata["longitude"]
    )

    # Store proof information in database
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
    reported_start: str = Form(...),
    reported_end: str = Form(...),
    photo_verified: bool = Form(...),
    visual_match_confidence: float = Form(...),
    reason: str = Form(...)
):
    """
    Combine backend verification with AI visual verification.

    Backend verifies:
    - Photo location
    - Photo timestamp

    AI module provides:
    - Photo/activity visual verification
    - Visual match confidence
    - Verification reason
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Get the latest uploaded proof for this activity
    cursor.execute("""
        SELECT
            id,
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

    proof_id = proof[0]
    location_verified = bool(proof[1])
    photo_timestamp = proof[5]

    # Verify photo timestamp against reported activity period
    timestamp_verified = verify_photo_timestamp(
        photo_timestamp=photo_timestamp,
        reported_start=reported_start,
        reported_end=reported_end
    )

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

    # Save final verification result
    cursor.execute("""
        UPDATE visual_proofs
        SET
            photo_verified = ?,
            timestamp_verified = ?,
            visual_match_confidence = ?,
            overall_confidence = ?,
            verification_status = ?,
            verification_reason = ?
        WHERE id = ?
    """, (
        int(result["photo_verified"]),
        int(result["timestamp_verified"]),
        result["visual_match_confidence"],
        result["overall_confidence"],
        result["status"],
        result["reason"],
        proof_id
    ))

    connection.commit()
    connection.close()

    return result