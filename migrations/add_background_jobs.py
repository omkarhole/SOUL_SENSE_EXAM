"""
Add background_jobs table for async task tracking.

This migration creates the background_jobs table used by the Background Task Queue
system to track long-running operations like PDF exports, email sending, etc.

Run with: python migrations/add_background_jobs.py
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index, ForeignKey, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime


def run_migration():
    """Create the background_jobs table."""
    from app.db import engine
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS background_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id VARCHAR(36) UNIQUE NOT NULL,
        user_id INTEGER NOT NULL REFERENCES users(id),
        task_type VARCHAR(50) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
        progress INTEGER DEFAULT 0,
        params TEXT,
        result TEXT,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        started_at DATETIME,
        completed_at DATETIME,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
    """
    
    # Create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_background_jobs_job_id ON background_jobs(job_id)",
        "CREATE INDEX IF NOT EXISTS idx_background_jobs_user_id ON background_jobs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status)",
        "CREATE INDEX IF NOT EXISTS idx_background_jobs_user_status ON background_jobs(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_background_jobs_created ON background_jobs(created_at)"
    ]
    
    with engine.connect() as conn:
        # Create table
        print("Creating background_jobs table...")
        conn.execute(text(create_table_sql))
        conn.commit()
        print("✓ Table created successfully")
        
        # Create indexes
        print("Creating indexes...")
        for index_sql in create_indexes_sql:
            try:
                conn.execute(text(index_sql))
                conn.commit()
            except Exception as e:
                print(f"  Index may already exist: {e}")
        print("✓ Indexes created successfully")
        
        print("\n✓ Migration completed: background_jobs table is ready")


def check_table_exists():
    """Check if the background_jobs table exists."""
    from app.db import engine
    
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='background_jobs'"
        ))
        return result.fetchone() is not None


if __name__ == "__main__":
    if check_table_exists():
        print("background_jobs table already exists. Skipping migration.")
    else:
        run_migration()
