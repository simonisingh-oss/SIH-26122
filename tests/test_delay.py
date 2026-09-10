from backend.app.intelligence.delay import analyze_delay


result = analyze_delay(
    "2026-09-13",
    "2026-09-18",
    "2026-09-12",
    "2026-09-16"
)

print("Delay Analysis:")
print(result)