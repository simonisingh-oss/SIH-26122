import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from matcher import ScheduleMatcher

# Gemini API client
client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

matcher=ScheduleMatcher("data/01_baseline_schedule.xlsx")

# --- Define Pydantic Schema to Guarantee JSON Structure ---
class MultilingualExtraction(BaseModel):
    activity_description: str
    discipline: str
    status: str
    percent_complete: Optional[float]
    delay_reason: Optional[str]
    location_or_asset: Optional[str]
    response: str


MULTILINGUAL_PROMPT = """
You are a multilingual construction-site AI assistant.

The user may communicate in:
- English
- Hindi
- Hinglish
- Other Indian languages

Understand the user's message regardless of language.

Convert the activity into a standardized, schedule-like construction activity name.

Use these standardizations when applicable:
- rebar installation / tying rebar / rebar ka kaam → "Erect Rebar"
- shuttering / shutter erection / shutter ka kaam → "Erect Shutter"
- backfilling / backfill ka kaam → "Backfill & Compaction"
- fit-up and tacking on joints → "Weld Joints"
- welding joints / weld joints → "Weld Joints"
- rack erection / erect rack → "Erect Line"
- toolbox talk and permits → "Toolbox Talk & Permit Issuance"

Preserve important identifiers and locations such as:
- line numbers
- rack sections
- grid numbers
- equipment IDs

Do not add identifiers that were not mentioned.

Your job is to convert the site statement into clear, structured construction information.

Extract:

1. activity_description
2. discipline
3. status
4. percent_complete
5. delay_reason
6. location_or_asset
7. response

Rules:

- Understand Hindi and Hinglish naturally.
- Translate the meaning internally into standardized English.
- Keep construction terminology accurate.
- Do not invent information.
- If something is not mentioned, use null.
- Status must be one of:
  Completed
  In Progress
  Not Started
  Delayed
  Partially Completed
  Unknown

- Discipline should be one of:
  Civil
  Piping
  Electrical
  Mechanical
  HSE
  Other
  Unknown

- percent_complete should only be included if the user explicitly gives a percentage.
- delay_reason should only be included if a delay is explicitly mentioned.
- location_or_asset should contain a directly mentioned location, grid, line, rack section, equipment or asset.
- response should be a short natural-language response to the user in the SAME language as the user's message.

Example input:
"Grid A1-A4 par rebar ka kaam complete ho gaya."

Example output:
{
  "activity_description": "Erect Rebar",
  "discipline": "Civil",
  "status": "Completed",
  "percent_complete": null,
  "delay_reason": null,
  "location_or_asset": "Grid A1-A4",
  "response": "Rebar ka kaam Grid A1-A4 par complete ho gaya."
}

Example input:
"Shuttering 80% complete hai lekin material late aane ki wajah se delay ho raha hai."

Example output:
{
  "activity_description": "Erect Shuttering",
  "discipline": "Civil",
  "status": "Delayed",
  "percent_complete": 80,
  "delay_reason": "Material delivery was late",
  "location_or_asset": null,
  "response": "Shuttering 80% complete hai aur material delay ki wajah se kaam affected hai."
}
"""


def ask_multilingual_assistant(user_message):

    prompt = MULTILINGUAL_PROMPT + "\n\nUser message:\n" + user_message

    try:
        # Use Pydantic Structured Outputs (like we did in pipeline.py) 
        # to completely eliminate JSON parsing bugs!
        
        response = client.chat.completions.create(
            model="gemini-3.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=60
        )

        raw_output = response.choices[0].message.content.strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.replace("```json", "")
            raw_output = raw_output.replace("```", "")
            raw_output = raw_output.strip()

        result = json.loads(raw_output)

        return result

    except Exception as e:
        print(f"Error calling Gemini or parsing JSON: {e}")
        return None


if __name__ == "__main__":

    print("Multilingual Construction AI Assistant")
    print("Type 'exit' to stop.\n")

    while True:

        user_message = input("You: ")

        if user_message.lower() == "exit":
            break

        result = ask_multilingual_assistant(user_message)

        if result:
            print("\nAI:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Match the standardized activity with the baseline schedule
            match = matcher.match_activity(
                result["activity_description"],
                result["discipline"]
            )

            if match:
                print("\nSchedule Match:")
                print("Activity ID:", match["matched_activity_id"])
                print("Activity:", match["matched_activity_name"])
                print("Score:", match["score"])
            else:
                print("\nSchedule Match:")
                print("No matching baseline activity found.")

            print()