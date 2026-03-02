"""
Migration: Add onboarding_completed column to users table
Issue #933: Onboarding Wizard

This migration adds the onboarding_completed boolean column to the users table.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models import Base, User
from sqlalchemy import create_engine, Column, Boolean, inspect
from sqlalchemy.orm import Session


def migration_add_onboarding_completed():
    """
    Add onboarding_completed column to users table.
    """
    db_path = project_root / "database.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'onboarding_completed' in columns:
            print("✅ Column 'onboarding_completed' already exists")
            return True
        
        # Add the column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0 NOT NULL
        """)
        
        conn.commit()
        print("✅ Successfully added 'onboarding_completed' column to users table")
        
        # Verify
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'onboarding_completed' in columns:
            print("✅ Verification passed: column exists")
            return True
        else:
            print("❌ Verification failed: column not found after migration")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        conn.close()


def migration_remove_onboarding_completed():
    """
    Remove onboarding_completed column (for rollback).
    Note: SQLite doesn't support DROP COLUMN directly, so we need to recreate the table.
    """
    print("⚠️  Rollback not implemented for SQLite (requires table recreation)")
    print("   To rollback, restore from backup or manually recreate the table.")
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Onboarding migration script")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        migration_remove_onboarding_completed()
    else:
        success = migration_add_onboarding_completed()
        sys.exit(0 if success else 1)
