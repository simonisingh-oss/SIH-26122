from visual_verifier import verify_photo


def run_visual_verification(activity_description, image_path):
    """
    Runs AI-based visual verification for a construction-site image.
    """

    result = verify_photo(
        activity_description=activity_description,
        image_path=image_path
    )

    return {
        "photo_verified": result["photo_verified"],
        "visual_match_confidence": result["visual_match_confidence"],
        "reason": result["reason"]
    }


if __name__ == "__main__":
    activity = "Erect Shuttering - Elevated Slab or Beam"

    image = (
        r"data\visual_verification\images\shuttering"
        r"\shuttering_01.jpeg"
    )

    verification_result = run_visual_verification(
        activity_description=activity,
        image_path=image
    )

    print("\nVISUAL VERIFICATION RESULT")
    print("==========================")
    print(verification_result)