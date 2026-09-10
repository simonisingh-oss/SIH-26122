from fastapi import FastAPI

from .intelligence.delay import analyze_delay
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

    activity_data = activity.model_dump()

    results = find_top_matches(
        activity_data,
        top_k=3
    )

    best_match = results[0]

    # Delay analysis is performed only when actual dates are available.
    if (
        activity.actual_start
        and activity.actual_end
        and best_match["planned_start"]
        and best_match["planned_end"]
    ):
        delay_analysis = analyze_delay(
            activity.actual_start,
            activity.actual_end,
            best_match["planned_start"],
            best_match["planned_end"],
            activity.status
        )

        final_status = delay_analysis["status"]

    else:
        final_status = activity.status

    return {
        "activity_description": activity.activity_description,
        "discipline": activity.discipline,
        "asset_id": activity.asset_id,
        "actual_start": activity.actual_start,
        "actual_end": activity.actual_end,
        "status": final_status,
        "delay_reason": activity.delay_reason,
        "source": activity.source,
        "confidence": best_match["confidence"]
    }