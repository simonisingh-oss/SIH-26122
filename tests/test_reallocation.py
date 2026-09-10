from backend.app.intelligence.reallocation import suggest_reallocation


activity = {
    "activity_description": "Cable tray installation",
    "discipline": "Electrical",
    "asset_id": "UNIT-B"
}

absent_workers = [
    {
        "worker_id": "W-101",
        "discipline": "Electrical"
    }
]

available_workers = [
    {
        "worker_id": "W-205",
        "discipline": "Electrical"
    },
    {
        "worker_id": "W-310",
        "discipline": "Civil"
    }
]

result = suggest_reallocation(
    activity,
    absent_workers,
    available_workers
)

print("Reallocation Analysis:")
print(result)