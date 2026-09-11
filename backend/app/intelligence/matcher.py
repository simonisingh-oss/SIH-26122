import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

BASELINE_CSV = "data/01_baseline_schedule.xlsx"

model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))

def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())

def construction_term_boost(text1, text2):
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    boost = 0.0

    # Rebar installation terminology
    if "rebar" in text1 and "rebar" in text2:
        boost += 0.20

    # Fit-up / tacking are part of the welding activity
    if (
        ("fit up" in text1 or "tacking" in text1 or "tack welding" in text1)
        and "weld" in text2
    ):
        boost += 0.20

    return boost

def token_overlap(text1, text2):
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)

    return len(intersection) / len(words1.union(words2))

def extract_identifiers(text):
    text = str(text)
    patterns = [
        r"\b\d{2}-[A-Z]{2}-\d{4}-[A-Z0-9]+\b",
        r"\b[A-Z]{1,5}-\d{2,5}\b",
        r"\b[A-Z]{1,3}\d{1,4}(?:-[A-Z]{1,3}\d{1,4})?\b"
    ]
    identifiers = set()
    for pattern in patterns:
        matches = re.findall(pattern, text.upper())
        identifiers.update(matches)
    return identifiers

def extract_sections(text):
    text = str(text).upper()
    sections = set()
    patterns = [
        r"\bRACK\s+SECTION\s+\d+\b",
        r"\bRACK\s+SEC\s+\d+\b",
        r"\bGRID\s+[A-Z0-9]+(?:-[A-Z0-9]+)?\b"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Normalize SEC to SECTION so they intersect correctly
            match = re.sub(r"\bRACK\s+SEC\b", "RACK SECTION", match)
            sections.add(match)
    return sections

def section_compatibility(text1, text2):
    sections1 = extract_sections(text1)
    sections2 = extract_sections(text2)

    if not sections1 or not sections2:
        return None

    if sections1.intersection(sections2):
        return 1.0

    return 0.0

def identifier_overlap(text1, text2):
    ids1 = extract_identifiers(text1)
    ids2 = extract_identifiers(text2)

    if not ids1 or not ids2:
        return 0.0

    return 1.0 if ids1.intersection(ids2) else 0.0

class ScheduleMatcher:

    def __init__(self, schedule_path):
        self.schedule = pd.read_excel(schedule_path)
        self.schedule["Activity_Name"] = (
            self.schedule["Activity_Name"]
            .fillna("")
            .astype(str)
        )
        self.schedule_embeddings = model.encode(
            self.schedule["Activity_Name"].tolist()
        )

    def match_activity(self, activity_description, discipline=None):
        activity_embedding = model.encode(activity_description)
        candidates = []

        for index, row in self.schedule.iterrows():
            schedule_name = row["Activity_Name"]
            schedule_discipline = str(row["Discipline"])

            semantic_score = cosine_similarity(
                activity_embedding,
                self.schedule_embeddings[index]
            )

            lexical_score = token_overlap(
                activity_description,
                schedule_name
            )

            identifier_score = identifier_overlap(
                activity_description,
                schedule_name
            )

            section_score = section_compatibility(
                activity_description,
                schedule_name
            )

            if section_score == 0.0:
                continue

            if identifier_score == 1.0:
                combined_score = (
                    0.40 * semantic_score +
                    0.20 * lexical_score +
                    0.40 * identifier_score
                )
            else:
                combined_score = (
                    0.60 * semantic_score +
                    0.40 * lexical_score
                )

            if section_score == 1.0:
                combined_score += 0.10

            if discipline:
                if discipline.lower() == schedule_discipline.lower():
                    combined_score += 0.10

            combined_score += construction_term_boost(
                activity_description,
                schedule_name
            )

            candidates.append({
                "score": combined_score,
                "semantic_score": semantic_score,
                "lexical_score": lexical_score,
                "identifier_score": identifier_score,
                "section_score": section_score,
                "activity_id": row.get("Activity_ID", ""),
                "activity_name": schedule_name,
                "discipline": schedule_discipline
            })

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        best = candidates[0] if candidates else None
        second = candidates[1] if len(candidates) > 1 else None
        second_score = second["score"] if second else 0.0
        gap = best["score"] - second_score if best else 0.0

        if not best:
            return None

        return {
            "input": activity_description,
            "matched_activity_id": best["activity_id"],
            "matched_activity_name": best["activity_name"],
            "matched_discipline": best["discipline"],
            "score": round(best["score"], 4),
            "second_best_score": round(second_score, 4),
            "score_gap": round(gap, 4),
            "semantic_score": round(best["semantic_score"], 4),
            "lexical_score": round(best["lexical_score"], 4),
            "identifier_score": round(best["identifier_score"], 4),
            "section_score": best["section_score"]
        }

if __name__ == "__main__":
    matcher = ScheduleMatcher(BASELINE_CSV)

    test_activities = [
        ("Erect Line 24-PL-1004-CS1A (Suction Hdr) Rack Section 3", "Piping"),
        ("Weld Joints - Line 24-PL-1004-CS1A (Suction Hdr) Rack Sec 3", "Piping"),
        ("Hydrotest - Line 24-PL-1004-CS1A (Suction Hdr)", "Piping"),
        ("Toolbox Talk & Permit Issuance - Compressor Bldg Area", "HSE"),
        ("Backfill & Compaction - Foundation Grid A1-A4", "Civil"),
        ("New Tie-in Line 10-PL-2051 Rack Sec 2 (unplanned scope)", "Piping")
    ]

    for activity, discipline in test_activities:
        result = matcher.match_activity(activity, discipline)
        if result:
            print(f"\nActivity: {result['input']}")
            print(f"Matched ID: {result['matched_activity_id']} | Name: {result['matched_activity_name']}")
            print(f"Discipline: {result['matched_discipline']}")
            print(f"Score: {result['score']} (Gap: {result['score_gap']})")
            print(f"Semantic: {result['semantic_score']} | Lexical: {result['lexical_score']} | Identifier: {result['identifier_score']}")
            print(f"Section: {result['section_score']}")
            print("-" * 70)
