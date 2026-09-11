import os
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List
from prompt import PROMPT

class Activity(BaseModel):
    activity_description: str
    discipline: str
    asset_id: Optional[str]
    actual_start: Optional[str]
    actual_end: Optional[str]
    status: str
    percent_complete: Optional[float]
    delay_reason: Optional[str]
    source: str
    evidence: str
    confidence: float

class ReportExtraction(BaseModel):
    activities: List[Activity]

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Read the report
with open("data/02_daily_progress_report_civil_piping.txt", "r") as file:
    report_text = file.read()

# We use PROMPT.format to replace the placeholders `{report_date}` and `{report_text}`
formatted_prompt = PROMPT.format(
    report_date="18-Jul-2026",
    report_text=report_text
)

# Send formatted prompt to LLM
# Use a real model like 'gpt-4o' and Pydantic structured outputs
response = client.chat.completions.create(
    model="gemini-3.5-flash",
    messages=[
        {
            "role": "user",
            "content": formatted_prompt
        }
    ]
)

print(response.choices[0].message.content)