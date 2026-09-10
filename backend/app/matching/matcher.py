from datetime import date
import re
from functools import lru_cache
import math

from ..database import get_connection

from .normalizer import normalize_text
from .similarity import text_similarity
from .confidence import confidence_level
from .embedding import create_embedding


def load_schedule():
    connection = get_connection()
    connection.row_factory = lambda cursor, row: {
        column[0]: row[index]
        for index, column in enumerate(cursor.description)
    }

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            schedule_activity_id,
            wbs_id,
            activity_description,
            discipline,
            asset_id,
            planned_start,
            planned_end
        FROM schedule_activities
    """)

    activities = cursor.fetchall()
    connection.close()

    return activities


def date_overlap_score(execution_activity, schedule_activity):
    actual_start = execution_activity.get("actual_start")
    actual_end = execution_activity.get("actual_end")

    planned_start = schedule_activity.get("planned_start")
    planned_end = schedule_activity.get("planned_end")

    if not actual_start or not actual_end or not planned_start or not planned_end:
        return 0.5

    actual_start = date.fromisoformat(str(actual_start).split(" ")[0])
    actual_end = date.fromisoformat(str(actual_end).split(" ")[0])
    planned_start = date.fromisoformat(str(planned_start).split(" ")[0])
    planned_end = date.fromisoformat(str(planned_end).split(" ")[0])

    if actual_start <= planned_end and actual_end >= planned_start:
        return 1.0

    if actual_start > planned_end:
        gap = (actual_start - planned_end).days
    else:
        gap = (planned_start - actual_end).days

    if gap <= 3:
        return 0.5

    return 0.0


def keyword_similarity(text1, text2):
    words1 = set(re.findall(r"\b[a-zA-Z0-9-]+\b", text1.lower()))
    words2 = set(re.findall(r"\b[a-zA-Z0-9-]+\b", text2.lower()))

    stopwords = {
        "the", "and", "for", "at", "in", "of", "to",
        "is", "on", "with", "work", "completed", "started",
        "installation", "activity"
    }

    words1 -= stopwords
    words2 -= stopwords

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def location_similarity(execution_activity, schedule_activity):
    execution_text = normalize_text(
        execution_activity.get("activity_description", "")
    )

    schedule_text = normalize_text(
        schedule_activity.get("activity_description", "")
    )

    location_patterns = [
        r"grid\s+[a-z0-9-]+",
        r"unit[-\s]?[a-z0-9]+",
        r"area[-\s]?[a-z0-9]+",
        r"section\s+[a-z0-9-]+",
        r"rack\s+section\s+[a-z0-9-]+",
        r"line\s+[0-9a-z-]+"
    ]

    execution_locations = set()

    for pattern in location_patterns:
        execution_locations.update(
            re.findall(pattern, execution_text)
        )

    schedule_locations = set()

    for pattern in location_patterns:
        schedule_locations.update(
            re.findall(pattern, schedule_text)
        )

    if not execution_locations or not schedule_locations:
        return 0.5

    if execution_locations.intersection(schedule_locations):
        return 1.0

    return 0.0


@lru_cache(maxsize=1000)
def get_cached_embedding(text):
    if not text:
        return []

    return create_embedding(text)


def cosine_similarity(vector1, vector2):
    if not vector1 or not vector2:
        return 0.0

    if len(vector1) != len(vector2):
        return 0.0

    dot_product = sum(
        a * b for a, b in zip(vector1, vector2)
    )

    magnitude1 = math.sqrt(
        sum(a * a for a in vector1)
    )

    magnitude2 = math.sqrt(
        sum(b * b for b in vector2)
    )

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    similarity = dot_product / (magnitude1 * magnitude2)

    return max(0.0, min(1.0, similarity))


def semantic_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0

    embedding1 = get_cached_embedding(text1)
    embedding2 = get_cached_embedding(text2)

    return cosine_similarity(
        embedding1,
        embedding2
    )


def calculate_match_score(execution_activity, schedule_activity):
    """
    Calculate matching score using:

    Semantic similarity = 30%
    Description similarity = 25%
    Keyword similarity = 15%
    Discipline = 20%
    Location = 7%
    Date compatibility = 3%
    """

    execution_description = normalize_text(
        execution_activity.get("activity_description", "")
    )

    schedule_description = normalize_text(
        schedule_activity.get("activity_description", "")
    )

    text_score = text_similarity(
        execution_description,
        schedule_description
    )

    keyword_score = keyword_similarity(
        execution_description,
        schedule_description
    )

    semantic_score = semantic_similarity(
        execution_description,
        schedule_description
    )

    execution_discipline = normalize_text(
        execution_activity.get("discipline", "")
    )

    schedule_discipline = normalize_text(
        schedule_activity.get("discipline", "")
    )

    discipline_score = 1.0 if (
        execution_discipline
        and execution_discipline == schedule_discipline
    ) else 0.0

    location_score = location_similarity(
        execution_activity,
        schedule_activity
    )

    date_score = date_overlap_score(
        execution_activity,
        schedule_activity
    )

    final_score = (
        0.30 * semantic_score
        + 0.25 * text_score
        + 0.15 * keyword_score
        + 0.20 * discipline_score
        + 0.07 * location_score
        + 0.03 * date_score
    )

    return round(final_score, 3)


def find_top_matches(execution_activity, top_k=3):
    schedule = load_schedule()

    candidates = []

    for activity in schedule:
        score = calculate_match_score(
            execution_activity,
            activity
        )

        candidates.append({
            "schedule_activity_id": activity["schedule_activity_id"],
            "activity_description": activity["activity_description"],
            "planned_start": activity["planned_start"],
            "planned_end": activity["planned_end"],
            "score": score,
            "confidence": confidence_level(score)
        })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:top_k]


def find_best_match(execution_activity):
    matches = find_top_matches(
        execution_activity,
        top_k=1
    )

    if not matches:
        return None

    return matches[0]