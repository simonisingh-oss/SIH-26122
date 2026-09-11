import io
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from .database import get_db, create_tables, ScheduleActivity, ExecutionReport
from .init_db import import_schedule_excel
from .intelligence.delay import analyze_delay
from .intelligence.reallocation import suggest_reallocation
from .matching.matcher import find_top_matches
from .schemas.activity import (
    ActivityRequest,
    ScheduleActivitySchema,
    ScheduleImportSummary,
    ExecutionReportResponse,
    MatchCandidate
)
from .geotagged_proof.router import router as visual_proof_router

app = FastAPI(
    title="SIH-26122 Infrastructure Planning-to-Execution Bridge API",
    version="1.0.0",
    description="Oil India Limited Backend API connecting L5/L6 baseline schedule activities with AI/NLP extracted site execution reports."
)
app.include_router(visual_proof_router)


@app.on_event("startup")
def startup_event():
    """Create database tables on startup if they don't exist."""
    create_tables()


@app.get("/", tags=["Health"])
def home():
    return {
        "status": "online",
        "message": "SIH-26122 Activity Matching API is running"
    }


# ==========================================
# SCHEDULE ACTIVITIES ENDPOINTS (/api/v1)
# ==========================================

@app.get("/api/v1/activities", response_model=List[ScheduleActivitySchema], tags=["Schedule Activities"])
@app.get("/activities", response_model=List[ScheduleActivitySchema], tags=["Schedule Activities"], include_in_schema=False)
def get_activities(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    level: Optional[str] = Query(None, description="Filter by level"),
    status: Optional[str] = Query(None, description="Filter by schedule status"),
    search: Optional[str] = Query(None, description="Search activity description"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: Session = Depends(get_db)
):
    """List planned L5/L6 schedule activities with pagination and filtering."""
    query = db.query(ScheduleActivity)
    if discipline:
        query = query.filter(ScheduleActivity.discipline.ilike(f"%{discipline}%"))
    if level:
        query = query.filter(ScheduleActivity.level.ilike(f"%{level}%"))
    if status:
        query = query.filter(ScheduleActivity.schedule_status.ilike(f"%{status}%"))
    if search:
        query = query.filter(ScheduleActivity.activity_description.ilike(f"%{search}%"))

    activities = query.offset(skip).limit(limit).all()
    return activities


@app.get("/api/v1/activities/{schedule_activity_id}", response_model=ScheduleActivitySchema, tags=["Schedule Activities"])
@app.get("/activities/{schedule_activity_id}", response_model=ScheduleActivitySchema, tags=["Schedule Activities"], include_in_schema=False)
def get_activity_by_id(schedule_activity_id: str, db: Session = Depends(get_db)):
    """Retrieve a single planned L5/L6 schedule activity by ID."""
    activity = db.query(ScheduleActivity).filter(
        ScheduleActivity.schedule_activity_id == schedule_activity_id
    ).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule activity '{schedule_activity_id}' not found."
        )
    return activity


@app.post("/api/v1/schedule/import", response_model=ScheduleImportSummary, tags=["Schedule Import"])
@app.post("/schedule/import", response_model=ScheduleImportSummary, tags=["Schedule Import"], include_in_schema=False)
async def import_schedule(file: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    """
    Import or update baseline L5/L6 schedule activities from an Excel file.
    Falls back to default data/01_baseline_schedule.xlsx if no file is provided.
    """
    if file:
        contents = await file.read()
        file_bytes = io.BytesIO(contents)
        return import_schedule_excel(file_bytes, db_session=db)

    from .init_db import SCHEDULE_FILE
    if not SCHEDULE_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Default baseline schedule file not found at {SCHEDULE_FILE}"
        )
    return import_schedule_excel(SCHEDULE_FILE, db_session=db)


# ==========================================
# EXECUTION REPORT & MATCHING ENDPOINTS (/api/v1)
# ==========================================

def process_execution_report(activity: ActivityRequest, db: Session) -> Dict[str, Any]:
    """Helper function to execute matching, delay analysis, and store execution reports."""
    # 1. Execute matching algorithm safely
    try:
        match_candidates = find_top_matches(activity.model_dump(), top_k=3)
    except Exception:
        match_candidates = []

    # Defensive check: never access results[0] without checking existence
    best_match = match_candidates[0] if match_candidates else None

    matched_activity_schema = None
    matched_id = None
    matched_desc = None
    confidence = "No Match"
    match_score = 0.0
    delay_days = 0
    resulting_status = activity.status

    if best_match:
        matched_id = best_match.get("schedule_activity_id")
        confidence = best_match.get("confidence", "Low")
        match_score = best_match.get("score", 0.0)

        # Query matched planned schedule activity from DB
        matched_db_act = db.query(ScheduleActivity).filter(
            ScheduleActivity.schedule_activity_id == matched_id
        ).first()

        if matched_db_act:
            matched_desc = matched_db_act.activity_description
            matched_activity_schema = ScheduleActivitySchema.model_validate(matched_db_act)

            # Perform delay analysis safely
            if (activity.actual_start and activity.actual_end and
                    matched_db_act.planned_start and matched_db_act.planned_end):
                try:
                    delay_res = analyze_delay(
                        activity.actual_start,
                        activity.actual_end,
                        matched_db_act.planned_start,
                        matched_db_act.planned_end,
                        activity.status
                    )
                    resulting_status = delay_res.get("status", activity.status)
                    delay_days = delay_res.get("delay_days", 0)
                except Exception:
                    resulting_status = activity.status
                    delay_days = 0

    # 2. Persist execution report separately in execution_reports table
    report_record = ExecutionReport(
        activity_description=activity.activity_description,
        discipline=activity.discipline,
        asset_id=activity.asset_id,
        actual_start=activity.actual_start,
        actual_end=activity.actual_end,
        status=resulting_status,
        delay_reason=activity.delay_reason,
        source=activity.source,
        matched_schedule_activity_id=matched_id,
        matched_activity_description=matched_desc,
        confidence_score=match_score,
        confidence_level=confidence,
        delay_days=delay_days
    )

    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    top_matches_formatted = [
        MatchCandidate(
            schedule_activity_id=m["schedule_activity_id"],
            activity_description=m["activity_description"],
            planned_start=m.get("planned_start"),
            planned_end=m.get("planned_end"),
            score=m["score"],
            confidence=m["confidence"]
        ) for m in match_candidates
    ]

    return {
        "id": report_record.id,
        "activity_description": report_record.activity_description,
        "discipline": report_record.discipline,
        "asset_id": report_record.asset_id,
        "actual_start": report_record.actual_start,
        "actual_end": report_record.actual_end,
        "status": report_record.status,
        "delay_reason": report_record.delay_reason,
        "source": report_record.source,
        "matched_schedule_activity_id": matched_id,
        "matched_activity_description": matched_desc,
        "confidence_level": confidence,
        "confidence_score": match_score,
        "delay_days": delay_days,
        "matched_activity": matched_activity_schema,
        "top_matches": top_matches_formatted
    }


@app.post("/api/v1/execution-reports", response_model=ExecutionReportResponse, tags=["Execution Reports"])
def create_execution_report(activity: ActivityRequest, db: Session = Depends(get_db)):
    """
    Ingest site execution JSON from AI/NLP team.
    Validates, matches with schedule, stores in execution_reports table, and returns matched result.
    """
    return process_execution_report(activity, db)


@app.get("/api/v1/execution-reports", response_model=List[ExecutionReportResponse], tags=["Execution Reports"])
@app.get("/execution-reports", response_model=List[ExecutionReportResponse], tags=["Execution Reports"], include_in_schema=False)
def list_execution_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Retrieve all ingested site execution reports."""
    reports = db.query(ExecutionReport).offset(skip).limit(limit).all()
    results = []

    for r in reports:
        matched_schema = None
        if r.matched_schedule_activity_id:
            matched_act = db.query(ScheduleActivity).filter(
                ScheduleActivity.schedule_activity_id == r.matched_schedule_activity_id
            ).first()
            if matched_act:
                matched_schema = ScheduleActivitySchema.model_validate(matched_act)

        results.append(ExecutionReportResponse(
            id=r.id,
            activity_description=r.activity_description,
            discipline=r.discipline or "",
            asset_id=r.asset_id or "",
            actual_start=r.actual_start or "",
            actual_end=r.actual_end or "",
            status=r.status or "In Progress",
            delay_reason=r.delay_reason,
            source=r.source or "DPR",
            matched_schedule_activity_id=r.matched_schedule_activity_id,
            matched_activity_description=r.matched_activity_description,
            confidence_level=r.confidence_level,
            confidence_score=r.confidence_score,
            delay_days=r.delay_days,
            matched_activity=matched_schema,
            top_matches=[]
        ))

    return results


@app.post("/match", tags=["Matching"])
def match_activity(activity: ActivityRequest, db: Session = Depends(get_db)):
    """
    Backward-compatible POST /match endpoint. Accepts site execution request,
    stores report in database, runs matching, and returns result format expected by existing clients.
    """
    res = process_execution_report(activity, db)
    return {
        "activity_description": res["activity_description"],
        "discipline": res["discipline"],
        "asset_id": res["asset_id"],
        "actual_start": res["actual_start"],
        "actual_end": res["actual_end"],
        "status": res["status"],
        "delay_reason": res["delay_reason"],
        "source": res["source"],
        "confidence": res["confidence_level"],
        "matched_schedule_activity_id": res["matched_schedule_activity_id"]
    }