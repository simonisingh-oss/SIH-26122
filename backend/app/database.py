import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "schedule.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_activities (
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

    connection.commit()
    connection.close()