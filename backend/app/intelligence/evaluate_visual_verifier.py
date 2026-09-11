import csv
from visual_verifier import verify_photo


LABELS_PATH = (
    r"data\visual_verification\labels.csv"
)

IMAGE_FOLDER = (
    r"data\visual_verification\images\shuttering"
)


def evaluate():
    total = 0
    correct = 0

    with open(
        LABELS_PATH,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            image_name = row["image"]
            activity = row["activity"]
            expected = int(row["expected_verified"])

            image_path = (
                f"{IMAGE_FOLDER}\\{image_name}"
            )

            print("\n" + "=" * 70)
            print(f"Image: {image_name}")
            print(f"Activity: {activity}")
            print(f"Expected: {bool(expected)}")

            result = verify_photo(
                activity_description=activity,
                image_path=image_path
            )

            predicted = result["photo_verified"]

            print(f"Predicted: {predicted}")
            print(
                f"Confidence: "
                f"{result['visual_match_confidence']}"
            )
            print(f"Reason: {result['reason']}")

            total += 1

            if predicted == bool(expected):
                correct += 1
                print("Result: CORRECT")
            else:
                print("Result: INCORRECT")

    print("\n" + "=" * 70)
    print("FINAL EVALUATION")
    print("=" * 70)
    print(f"Total test cases: {total}")
    print(f"Correct predictions: {correct}")

    if total > 0:
        accuracy = (correct / total) * 100
        print(f"Accuracy: {accuracy:.2f}%")
    else:
        print("Accuracy: No test cases found.")


if __name__ == "__main__":
    evaluate()