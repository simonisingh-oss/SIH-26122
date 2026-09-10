from fastapi import FastAPI

from .intelligence.delay import analyze_delay
from .intelligence.reallocation import suggest_reallocation
from .matching.matcher import find_top_matches
from .schemas.activity import ActivityRequest


app = FastAPI(
    title="SIH-26122 Activity Matching API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Activity Matching API is running"
    }


@app.post("/match")
def match_activity(activity: ActivityRequest):

    results = find_top_matches(
        activity.model_dump(),
        top_k=3
    )

    best_match = results[0]

    delay_analysis = analyze_delay(
        activity.actual_start,
        activity.actual_end,
        best_match["planned_start"],
        best_match["planned_end"],
        activity.status
    )

    return {
        "activity_description": activity.activity_description,
        "discipline": activity.discipline,
        "asset_id": activity.asset_id,
        "actual_start": activity.actual_start,
        "actual_end": activity.actual_end,
        "status": delay_analysis["status"],
        "delay_reason": activity.delay_reason,
        "source": activity.source,
        "confidence": best_match["confidence"]
    }