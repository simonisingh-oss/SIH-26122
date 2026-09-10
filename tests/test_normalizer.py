from backend.app.matching.normalizer import normalize_text


test_cases = [
    "Foundation Excavation Work - Area A",
    "FOUNDATION excavation!! Area-A",
    "  Structural   Steel   Erection  ",
    "Cable Tray Installation"
]


for text in test_cases:
    print("Original :", text)
    print("Normalized:", normalize_text(text))
    print("-" * 50)