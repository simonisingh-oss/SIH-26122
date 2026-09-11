import os
import json
from openai import OpenAI
from proactive_intelligence import predict_risks
from pydantic import BaseModel
from typing import Optional, List
from prompt import PROMPT
from matcher import ScheduleMatcher
from normalizer import ActivityNormalizer, load_terminology


# Configuration
BASELINE_SCHEDULE = "data/01_baseline_schedule.xlsx"
REPORT_PATH = "data/02_daily_progress_report_civil_piping.txt"
TERMINOLOGY_CSV = "data/05_terminology_synonym_hints.csv"
MATCH_THRESHOLD = 0.40


# --- 1. Define Pydantic Schema for LLM Extraction ---

class Activity(BaseModel):
    activity_description: str
    discipline: str
    asset_id: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    status: str
    percent_complete: Optional[float] = None
    delay_reason: Optional[str] = None
    source: str
    evidence: str = ""
    confidence: float


class ReportExtraction(BaseModel):
    activities: List[Activity]


def run_pipeline():

    print("Loading Activity Normalizer...")
    terminology = load_terminology(TERMINOLOGY_CSV)
    normalizer = ActivityNormalizer(terminology)

    print("Loading Schedule Matcher...")
    matcher = ScheduleMatcher(BASELINE_SCHEDULE)

    print(f"Reading Report: {REPORT_PATH}")

    with open(REPORT_PATH, "r", encoding="utf-8") as file:
        report_text = file.read()

    # Format prompt
    formatted_prompt = PROMPT.format(
        report_date="18-Jul-2026",
        report_text=report_text
    )

    # --- 2. Gemini Client ---

    client = OpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    print("Calling Gemini for structured extraction...")

    response = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=[
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]
    )

    raw_output = response.choices[0].message.content

    print("Gemini extraction received.")

    parsed_json = json.loads(raw_output)

    # Gemini may return either:
    # 1. {"activities": [...]}
    # 2. [...]
    # Normalize both formats to {"activities": [...]}

    if isinstance(parsed_json, list):
        parsed_json = {
            "activities": parsed_json
        }

    # Fill in optional fields if Gemini omits them
    for activity in parsed_json.get("activities", []):
        activity.setdefault("percent_complete", None)
        activity.setdefault("evidence", "")

    extracted_data = ReportExtraction.model_validate(parsed_json)
    final_output = []

    print("Normalizing and Matching extracted activities...\n")


    # --- 3. Normalize + Match each activity ---

    for act in extracted_data.activities:

        # --- A. Terminology Normalization ---

        norm_result = normalizer.normalize_activity(
            act.activity_description
        )

        search_description = act.activity_description
        normalized_term_used = None

        if norm_result["confidence_tier"] in ["High", "Medium"]:

            normalized_term_used = norm_result["normalized_plan_term"]

            search_description = (
                f"{act.activity_description} - "
                f"{normalized_term_used}"
            )


        # --- B. Match against baseline schedule ---

        match_result = matcher.match_activity(
            search_description,
            act.discipline
        )


        # --- C. Decide matched Activity ID ---

        if (
            match_result is None
            or match_result["score"] < MATCH_THRESHOLD
        ):

            matched_id = "UNMATCHED_NEW_ACTIVITY"

            match_score = (
                None
                if match_result is None
                else match_result["score"]
            )

        else:

            matched_id = str(
                match_result["matched_activity_id"]
            )

            match_score = match_result["score"]


        # --- D. Combine everything ---

        combined_activity = act.model_dump()

        combined_activity["normalized_term_applied"] = (
            normalized_term_used
        )

        combined_activity["matched_activity_id"] = matched_id

        combined_activity["matcher_score"] = match_score

        final_output.append(combined_activity)

    # --- 3.5 Proactive Execution Intelligence ---

    print("Running Proactive Execution Intelligence...\n")

    predicted_risks = predict_risks(final_output)

    # --- 4. Final Output ---

    print("=" * 80)
    print("FINAL END-TO-END PIPELINE OUTPUT:")
    print("=" * 80)

    pipeline_result = {
        "activities": final_output,
        "predicted_risks": predicted_risks
    }

    output_json = json.dumps(
        pipeline_result,
        indent=2
    )

    print(output_json)


    # --- 5. Save output ---

    with open(
        "data/pipeline_output.json",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(output_json)

    print(
        "\nSaved output to "
        "data/pipeline_output.json"
    )


if __name__ == "__main__":
    run_pipeline()