import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "schedule.db"

# Environment-based database configuration
DEFAULT_DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ScheduleActivity(Base):
    __tablename__ = "schedule_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    schedule_activity_id = Column(String, unique=True, index=True, nullable=False)
    activity_description = Column(Text, nullable=False)
    discipline = Column(String, nullable=True)
    wbs_id = Column(String, nullable=True)
    level = Column(String, nullable=True)
    planned_start = Column(String, nullable=True)
    planned_end = Column(String, nullable=True)
    duration_days = Column(Integer, nullable=True)
    predecessor_id = Column(String, nullable=True)
    percent_complete = Column(Float, nullable=True)
    schedule_status = Column(String, nullable=True)
    asset_id = Column(String, nullable=True)


class ExecutionReport(Base):
    __tablename__ = "execution_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    activity_description = Column(Text, nullable=False)
    discipline = Column(String, nullable=True)
    asset_id = Column(String, nullable=True)
    actual_start = Column(String, nullable=True)
    actual_end = Column(String, nullable=True)
    status = Column(String, nullable=True)
    delay_reason = Column(Text, nullable=True)
    source = Column(String, default="DPR")
    matched_schedule_activity_id = Column(String, nullable=True)
    matched_activity_description = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    confidence_level = Column(String, nullable=True)
    delay_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PostgreSQLConnectionWrapper:
    """Wrapper to allow matcher.py's legacy cursor & row_factory usage on PostgreSQL connections."""
    def __init__(self, raw_conn):
        self._conn = raw_conn
        self.row_factory = None

    def cursor(self):
        cursor = self._conn.cursor()
        if self.row_factory:
            # Attach row_factory behavior to cursor fetchall
            orig_fetchall = cursor.fetchall
            row_factory = self.row_factory

            def custom_fetchall():
                rows = orig_fetchall()
                if not cursor.description:
                    return rows
                return [row_factory(cursor, row) for row in rows]

            cursor.fetchall = custom_fetchall
        return cursor

    def close(self):
        self._conn.close()

    def commit(self):
        self._conn.commit()


def get_connection():
    """
    Backward-compatible connection getter for matcher.py.
    Returns SQLite connection or wrapped PostgreSQL raw connection.
    """
    if DATABASE_URL.startswith("sqlite"):
        return sqlite3.connect(DB_PATH)
    raw = engine.raw_connection()
    return PostgreSQLConnectionWrapper(raw)