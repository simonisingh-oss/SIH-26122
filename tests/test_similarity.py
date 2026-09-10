from backend.app.matching.similarity import text_similarity


test_cases = [
    (
        "Foundation excavation completed",
        "Excavation for foundation"
    ),
    (
        "Structural steel erection",
        "Structural steel erection"
    ),
    (
        "Cable tray installation",
        "Foundation excavation"
    )
]


for text1, text2 in test_cases:

    score = text_similarity(text1, text2)

    print("Text 1:", text1)
    print("Text 2:", text2)
    print("Similarity:", round(score, 3))
    print("-" * 50)