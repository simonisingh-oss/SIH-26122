from pydantic import BaseModel, Field, ConfigDict
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


class ScheduleActivitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schedule_activity_id: str
    activity_description: str
    discipline: Optional[str] = None
    wbs_id: Optional[str] = None
    level: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    duration_days: Optional[int] = None
    predecessor_id: Optional[str] = None
    percent_complete: Optional[float] = None
    schedule_status: Optional[str] = None
    asset_id: Optional[str] = None


class ScheduleImportSummary(BaseModel):
    success: bool
    message: str
    total_rows: int
    imported_count: int
    skipped_count: int
    errors: List[str] = Field(default_factory=list)


class MatchCandidate(BaseModel):
    schedule_activity_id: str
    activity_description: str
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    score: float
    confidence: str


class ExecutionReportResponse(BaseModel):
    id: int

    activity_description: str
    discipline: str
    asset_id: str

    actual_start: str
    actual_end: str

    status: str
    delay_reason: Optional[str] = None
    source: str

    matched_schedule_activity_id: Optional[str] = None
    matched_activity_description: Optional[str] = None

    confidence_level: Optional[str] = None
    confidence_score: Optional[float] = None
    delay_days: Optional[int] = None

    matched_activity: Optional[ScheduleActivitySchema] = None
    top_matches: List[MatchCandidate] = Field(default_factory=list)