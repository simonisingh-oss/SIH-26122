import sqlite3
from pathlib import Path
import pandas as pd

from .database import DB_PATH, create_tables


BASE_DIR = Path(__file__).resolve().parents[2]
SCHEDULE_FILE = BASE_DIR / "data" / "01_baseline_schedule.xlsx"


def load_schedule():
    create_tables()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS schedule_activities")

    cursor.execute("""
        CREATE TABLE schedule_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_activity_id TEXT UNIQUE NOT NULL,
            activity_description TEXT NOT NULL,
            discipline TEXT,
            wbs_id TEXT,
            level TEXT,
            planned_start TEXT,
            planned_end TEXT,
            duration_days INTEGER,
            predecessor_id TEXT,
            percent_complete REAL,
            schedule_status TEXT,
            asset_id TEXT
        )
    """)

    df = pd.read_excel(SCHEDULE_FILE)
    df.columns = df.columns.astype(str).str.strip()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO schedule_activities (
                schedule_activity_id,
                activity_description,
                discipline,
                wbs_id,
                level,
                planned_start,
                planned_end,
                duration_days,
                predecessor_id,
                percent_complete,
                schedule_status,
                asset_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row["Activity_ID"]),
            str(row["Activity_Name"]),
            str(row["Discipline"]),
            str(row["WBS_Path"]),
            str(row.get("L Level", "")),
            str(row["Planned_Start"]),
            str(row["Planned_Finish"]),
            int(row["Duration_Days"]),
            None if pd.isna(row["Predecessor_ID"]) else str(row["Predecessor_ID"]),
            float(row["Percent_Complete"]),
            str(row["Schedule_Status"]),
            None
        ))

    connection.commit()
    connection.close()

    print("Real baseline schedule loaded successfully.")


if __name__ == "__main__":
    load_schedule()