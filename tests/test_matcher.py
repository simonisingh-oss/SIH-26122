from backend.app.matching.matcher import find_top_matches

test_activities = [
    {
        "activity_description": "Rebar and shuttering work at compressor building foundation Grid A1-A4",
        "discipline": "Civil",
        "asset_id": "Grid A1-A4",
        "actual_start": "2026-07-17",
        "actual_end": "2026-07-18"
    },
    {
        "activity_description": "Erection of suction header rack Section 3 for 24 inch line",
        "discipline": "Piping",
        "asset_id": "C-101",
        "actual_start": "2026-07-18",
        "actual_end": "2026-07-18"
    },
    {
        "activity_description": "Fit-up and tacking of suction header rack joints",
        "discipline": "Piping",
        "asset_id": "C-101",
        "actual_start": "2026-07-18",
        "actual_end": "2026-07-18"
    }
]

for activity in test_activities:

    results = find_top_matches(activity, top_k=3)

    print("\nActual Activity:")
    print(activity)

    print("\nTop 3 Matches:")

    for rank, result in enumerate(results, start=1):
        print(f"{rank}. {result}")

    print("-" * 60)