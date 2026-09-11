import io
import os
from pathlib import Path
from typing import Union, Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session

from .database import create_tables, SessionLocal, ScheduleActivity, engine, get_db

BASE_DIR = Path(__file__).resolve().parents[2]
SCHEDULE_FILE = BASE_DIR / "data" / "01_baseline_schedule.xlsx"


def safe_str(val: Any) -> Union[str, None]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    return s if s != "" and s.lower() != "nan" else None


def safe_int(val: Any, default: int = 0) -> int:
    if pd.isna(val) or val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    if pd.isna(val) or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_date_str(val: Any) -> Union[str, None]:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return None
    # If string contains time part e.g. "2026-09-01 00:00:00", split it
    return s.split(" ")[0]


def import_schedule_excel(
    file_source: Union[str, Path, io.BytesIO],
    db_session: Session = None
) -> Dict[str, Any]:
    """
    Reads, validates, cleans, and imports baseline schedule activities from Excel.
    Supports both file paths and byte streams (for API uploads).
    """
    create_tables()

    session = db_session if db_session else SessionLocal()
    should_close = db_session is None

    total_rows = 0
    imported_count = 0
    skipped_count = 0
    errors: List[str] = []

    try:
        df = pd.read_excel(file_source)
        df.columns = df.columns.astype(str).str.strip()

        # Flexible column mapping for variations in Excel naming
        col_map = {}
        for col in df.columns:
            normalized = col.lower().replace(" ", "_").replace("-", "_")
            col_map[normalized] = col

        # Determine activity ID column
        id_col = None
        for candidate in ["activity_id", "schedule_activity_id", "act_id", "code"]:
            if candidate in col_map:
                id_col = col_map[candidate]
                break

        # Determine description column
        desc_col = None
        for candidate in ["activity_name", "activity_description", "description", "name", "title"]:
            if candidate in col_map:
                desc_col = col_map[candidate]
                break

        if not id_col or not desc_col:
            missing = []
            if not id_col:
                missing.append("Activity_ID")
            if not desc_col:
                missing.append("Activity_Name")
            return {
                "success": False,
                "message": f"Excel missing required columns: {', '.join(missing)}",
                "total_rows": 0,
                "imported_count": 0,
                "skipped_count": 0,
                "errors": [f"Missing required column headers: {', '.join(missing)}"]
            }

        total_rows = len(df)

        for index, row in df.iterrows():
            row_num = index + 2  # Excel 1-indexed, header is row 1
            act_id = safe_str(row.get(id_col))
            desc = safe_str(row.get(desc_col))

            if not act_id or not desc:
                skipped_count += 1
                errors.append(f"Row {row_num}: Skipped due to missing Activity_ID or Activity_Name")
                continue

            discipline = safe_str(row.get(col_map.get("discipline")))
            wbs_id = safe_str(row.get(col_map.get("wbs_path", col_map.get("wbs_id"))))
            level = safe_str(row.get(col_map.get("l_level", col_map.get("l_level", col_map.get("level")))))
            planned_start = safe_date_str(row.get(col_map.get("planned_start", col_map.get("start"))))
            planned_end = safe_date_str(row.get(col_map.get("planned_finish", col_map.get("planned_end"))))
            duration = safe_int(row.get(col_map.get("duration_days", col_map.get("duration"))))
            predecessor = safe_str(row.get(col_map.get("predecessor_id", col_map.get("predecessor"))))
            percent_complete = safe_float(row.get(col_map.get("percent_complete", col_map.get("progress"))))
            status = safe_str(row.get(col_map.get("schedule_status", col_map.get("status")))) or "Not Started"
            asset_id = safe_str(row.get(col_map.get("asset_id", col_map.get("contractor"))))

            # Upsert into database
            existing = session.query(ScheduleActivity).filter(
                ScheduleActivity.schedule_activity_id == act_id
            ).first()

            if existing:
                existing.activity_description = desc
                existing.discipline = discipline
                existing.wbs_id = wbs_id
                existing.level = level
                existing.planned_start = planned_start
                existing.planned_end = planned_end
                existing.duration_days = duration
                existing.predecessor_id = predecessor
                existing.percent_complete = percent_complete
                existing.schedule_status = status
                if asset_id:
                    existing.asset_id = asset_id
            else:
                new_activity = ScheduleActivity(
                    schedule_activity_id=act_id,
                    activity_description=desc,
                    discipline=discipline,
                    wbs_id=wbs_id,
                    level=level,
                    planned_start=planned_start,
                    planned_end=planned_end,
                    duration_days=duration,
                    predecessor_id=predecessor,
                    percent_complete=percent_complete,
                    schedule_status=status,
                    asset_id=asset_id
                )
                session.add(new_activity)

            imported_count += 1

        session.commit()

        return {
            "success": True,
            "message": f"Successfully processed baseline schedule ({imported_count} activities imported/updated).",
            "total_rows": total_rows,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "errors": errors
        }

    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Error importing Excel file: {str(e)}",
            "total_rows": total_rows,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "errors": [str(e)]
        }
    finally:
        if should_close:
            session.close()


def load_schedule():
    """Legacy helper entry point for loading default schedule."""
    if not SCHEDULE_FILE.exists():
        print(f"File not found: {SCHEDULE_FILE}")
        return
    res = import_schedule_excel(SCHEDULE_FILE)
    print(res["message"])


if __name__ == "__main__":
    load_schedule()