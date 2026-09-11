from visual_verifier import verify_photo


IMAGE_PATH = (
    r"data\visual_verification\images\shuttering\shuttering_01.jpeg"
)

ACTIVITY_DESCRIPTION = (
    "Erect Rebar - Foundation Grid A1-A4"
)


result = verify_photo(
    activity_description=ACTIVITY_DESCRIPTION,
    image_path=IMAGE_PATH
)

print("\nVISUAL VERIFICATION RESULT:")
print(result)