
import os
from pathlib import Path
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent
database_url = f"sqlite:///{ROOT_DIR}/data/soulsense.db"
# Normalize to forward slashes for SQLAlchemy
database_url = database_url.replace('\\', '/')

print(f"Testing connection to: {database_url}")
print(f"Data directory exists: {os.path.exists(ROOT_DIR / 'data')}")
print(f"DB file exists: {os.path.exists(ROOT_DIR / 'data' / 'soulsense.db')}")

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Connection successful: {result.fetchone()}")
except Exception as e:
    print(f"Connection failed: {e}")
