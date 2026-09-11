import csv
import numpy as np
from sentence_transformers import SentenceTransformer

TERMINOLOGY_CSV = "data/05_terminology_synonym_hints.csv"

HIGH_CONFIDENCE_THRESHOLD = 0.90
MEDIUM_CONFIDENCE_THRESHOLD = 0.75
AMBIGUOUS_GAP_THRESHOLD = 0.05

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_terminology(csv_path):
    entries = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            entries.append({
                "discipline": row["discipline"].strip(),
                "field_term": row["field_term"].strip(),
                "plan_term": row["plan_term"].strip(),
                "notes": row.get("notes", "").strip()
            })

    return entries

def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class ActivityNormalizer:
    def __init__(self, terminology):
        self.terminology = terminology
        # Extract field terms
        self.field_terms = [entry["field_term"] for entry in terminology]
        # Pre-compute embeddings for ALL terminology ONLY ONCE
        self.term_embeddings = model.encode(self.field_terms)
        
    def normalize_activity(self, activity_description):
        # We only encode the new activity on each call
        activity_embedding = model.encode(activity_description)

        scored = []
        for entry, embedding in zip(self.terminology, self.term_embeddings):
            similarity = cosine_similarity(activity_embedding, embedding)
            scored.append((similarity, entry))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return {
                "input": activity_description,
                "matched_field_term": None,
                "normalized_plan_term": None,
                "discipline": None,
                "similarity": None,
                "second_best_similarity": None,
                "confidence_tier": "Unmatched"
            }

        best_score, best_entry = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0

        if best_score < MEDIUM_CONFIDENCE_THRESHOLD:
            tier = "Unmatched"
        elif best_score - second_score < AMBIGUOUS_GAP_THRESHOLD:
            tier = "Ambiguous"
        elif best_score >= HIGH_CONFIDENCE_THRESHOLD:
            tier = "High"
        else:
            tier = "Medium"

        return {
            "input": activity_description,
            "matched_field_term": best_entry["field_term"],
            "normalized_plan_term": best_entry["plan_term"],
            "discipline": best_entry["discipline"],
            "similarity": round(best_score, 4),
            "second_best_similarity": round(second_score, 4),
            "confidence_tier": tier
        }

if __name__ == "__main__":
    terminology = load_terminology(TERMINOLOGY_CSV)
    
    # Initialize the normalizer class so we encode the terminology once
    normalizer = ActivityNormalizer(terminology)

    test_activities = [
        "finished tying the rebar mat at the compressor building foundation",
        "crew only performed fit-up and tacking on the joints",
        "spool erected on rack section 3, all five spools placed",
        "conducted toolbox talk and issued two permits"
    ]

    for activity in test_activities:
        result = normalizer.normalize_activity(activity)

        print("Input:", result["input"])
        print("Matched field_term:", result["matched_field_term"])
        print("Normalized plan_term:", result["normalized_plan_term"])
        print("Discipline:", result["discipline"])
        print("Similarity:", result["similarity"])
        print("2nd best:", result["second_best_similarity"])
        print("Confidence:", result["confidence_tier"])
        print("-" * 60)
