from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ActivityRequest(BaseModel):

    activity_description: str

    discipline: str

    asset_id: str

    actual_start: str

    actual_end: str

    status: str

    delay_reason: Optional[str] = None

    source: str = "DPR"

    absent_workers: List[Dict] = Field(default_factory=list)

    available_workers: List[Dict] = Field(default_factory=list)