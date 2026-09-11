import csv
from matcher import ScheduleMatcher

GROUND_TRUTH_CSV = "data/04_ground_truth_extraction_matches.csv"
BASELINE_SCHEDULE = "data/01_baseline_schedule.xlsx"


def load_ground_truth(csv_path):
    rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append(row)

    return rows


if __name__ == "__main__":
    matcher = ScheduleMatcher(BASELINE_SCHEDULE)
    ground_truth = load_ground_truth(GROUND_TRUTH_CSV)

    total = len(ground_truth)
    correct = 0

    print("Ground-truth rows:", total)
    print("=" * 80)

    for i, row in enumerate(ground_truth, start=1):

        activity = row["extracted_activity_desc"].strip()
        discipline = row["discipline"].strip()

        expected_id = row["expected_matched_activity_id"].strip()
        expected_tier = row["expected_confidence_tier"].strip()

        result = matcher.match_activity(
            activity,
            discipline
        )

        print(f"\nCASE {i}")
        print("-" * 80)

        print("Activity:")
        print(activity)

        print("Discipline:")
        print(discipline)

        print("\nExpected:")
        print("Activity ID:", expected_id)
        print("Confidence Tier:", expected_tier)

        if result is None:
            print("\nMatcher result: NO MATCH")
            predicted_id = "UNMATCHED_NEW_ACTIVITY"
        else:
            # If the best score is very low, assume it's a new/unmatched activity
            if result["score"] < 0.40:  # You can tune this threshold
                predicted_id = "UNMATCHED_NEW_ACTIVITY"
                print("\nPredicted: UNMATCHED_NEW_ACTIVITY (Score was too low)")
            else:
                predicted_id = str(result["matched_activity_id"])
                print("\nPredicted:")
                print("Activity ID:", predicted_id)
                # ... print the rest of the stats ...

        # Check whether the predicted ID is correct
        if predicted_id == expected_id:
            print("\nMATCH: CORRECT")
            correct += 1
        else:
            print("\nMATCH: WRONG")

    accuracy = (correct / total) * 100 if total > 0 else 0

    print("\n")
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print("Total cases:", total)
    print("Correct matches:", correct)
    print("Wrong matches:", total - correct)
    print(f"Matching accuracy: {accuracy:.2f}%")
    print("=" * 80)