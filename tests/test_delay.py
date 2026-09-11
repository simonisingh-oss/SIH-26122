from backend.app.intelligence.delay import analyze_delay


def test_delay_analysis():
    result = analyze_delay(
        "2026-09-13",
        "2026-09-18",
        "2026-09-12",
        "2026-09-16",
        "Completed"
    )

    print("Delay Analysis:")
    print(result)

    assert result["status"] == "Delayed"
    assert result["delay_days"] == 2


if __name__ == "__main__":
    test_delay_analysis()