
from sqlalchemy import create_engine, text
from backend.fastapi.api.config import get_settings_instance
import os

settings = get_settings_instance()
url = settings.database_url
print(f"Testing URL: {url}")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO test DEFAULT VALUES"))
        res = conn.execute(text("SELECT * FROM test")).fetchall()
        print(f"Success! Data: {res}")
        conn.execute(text("DROP TABLE test"))
        conn.commit()
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
