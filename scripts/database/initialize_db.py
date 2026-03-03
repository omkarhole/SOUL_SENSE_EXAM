
import os
import sys
import sqlite3
from sqlalchemy import create_engine
from backend.fastapi.api.config import get_settings_instance
from backend.fastapi.api.models import Base

# Force TEMP directory to a simple path to avoid SQLite access issues
os.environ['TEMP'] = "C:\\temp_sqlite"
os.environ['TMP'] = "C:\\temp_sqlite"
if not os.path.exists("C:\\temp_sqlite"):
    os.makedirs("C:\\temp_sqlite", exist_ok=True)

settings = get_settings_instance()
url = settings.database_url
db_path = settings.database_url.replace("sqlite:///", "")

print(f"Initializing database at: {db_path}")

# 1. Clean up existing database files
for ext in ["", "-wal", "-shm", "-journal"]:
    f = db_path + ext
    if os.path.exists(f):
        print(f"Deleting {f}")
        try:
            os.remove(f)
        except Exception as e:
            print(f"Warning: Could not delete {f}: {e}")

# 2. Create tables using SQLAlchemy (Batch mode usually works better here)
try:
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    print("SQLAlchemy create_all successful")
except Exception as e:
    print(f"SQLAlchemy create_all failed: {e}. Trying native sqlite3 fallback.")
    # Fallback to a very minimal manual create if needed, but create_all should work if permissions are okay.
    raise

# 3. Manually insert the HEAD revision to satisfy Alembic
HEAD_REVISION = "d108d0b41e08"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
    cursor.execute("DELETE FROM alembic_version")
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (HEAD_REVISION,))
    conn.commit()
    conn.close()
    print(f"Stamped database with head revision: {HEAD_REVISION}")
except Exception as e:
    print(f"Failed to stamp database: {e}")
    sys.exit(1)

print("Database initialization COMPLETED SUCCESSFULLY!")
