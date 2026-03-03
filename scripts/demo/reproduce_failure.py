
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
from backend.fastapi.api.config import get_settings_instance
import os

settings = get_settings_instance()
url = settings.database_url
print(f"URL: {url}")

db_file = "data/soulsense.db"
if os.path.exists(db_file):
    print(f"Deleting existing DB file: {db_file}")
    os.remove(db_file)

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        print("Connected!")
        # Simulate Alembic's work
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR)"))
        print("Created users table")
        
        # Simulate batch-like operation (copy and move)
        conn.execute(text("CREATE TABLE _tmp_users (id INTEGER PRIMARY KEY, username VARCHAR)"))
        conn.execute(text("INSERT INTO _tmp_users SELECT * FROM users"))
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE _tmp_users RENAME TO users"))
        print("Completed simulated batch operation")
        
        conn.commit()
        print("Committed!")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
