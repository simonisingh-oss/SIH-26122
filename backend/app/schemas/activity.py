from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ActivityRequest(BaseModel):

    activity_description: str

    discipline: str

    asset_id: str

    actual_start: Optional[str] = None

    actual_end: Optional[str] = None

    status: str

    percent_complete: Optional[float] = None

    delay_reason: Optional[str] = None

    source: str = "DPR"

    evidence: Optional[str] = None

    confidence: Optional[float] = None

    normalized_term_applied: Optional[str] = None

    matched_activity_id: Optional[str] = None

    matcher_score: Optional[float] = None

    absent_workers: List[Dict] = Field(default_factory=list)

    available_workers: List[Dict] = Field(default_factory=list)