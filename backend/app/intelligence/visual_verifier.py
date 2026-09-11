import os
import base64
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- Define Pydantic Schema ---
from pydantic import BaseModel, Field


class VisualVerification(BaseModel):
    photo_verified: bool
    visual_match_confidence: float = Field(
        ge=0.0,
        le=1.0
    )
    reason: str


VISUAL_VERIFICATION_PROMPT = """
You are a construction-site visual verification assistant.

Your task is to check whether a construction site photo visually supports
the reported activity.

Reported activity:
{activity_description}

Rules:
1. photo_verified must be true only when the image provides reasonable
   visual evidence that the reported construction activity is being performed.
2. visual_match_confidence must be a number between 0 and 1.
3. Do not assume that an activity happened if there is no visible evidence.
4. If the image is unclear, unrelated, or does not provide enough evidence,
   set photo_verified to false and use a lower confidence.
5. Do not use GPS or timestamp information. Those are verified separately
   by the backend.
6. Do not invent details that cannot be seen in the image.
"""

def verify_photo(activity_description, image_path):
    """
    Verify whether a construction photo visually supports
    the reported activity.
    """
    
    # Dynamically determine mime type
    mime_type = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = VISUAL_VERIFICATION_PROMPT.format(
        activity_description=activity_description
    )

    try:
        response = client.beta.chat.completions.parse(
            model="gemini-3.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format=VisualVerification,
            timeout=60
        )

        result = response.choices[0].message.parsed
        return result.model_dump()
        
    except Exception as e:
        print(f"Error during visual verification: {e}")
        return {
            "photo_verified": False,
            "visual_match_confidence": 0.0,
            "reason": f"Verification failed: {str(e)}"
        }