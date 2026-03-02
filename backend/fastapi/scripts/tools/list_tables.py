
import sqlite3
import os

db_path = "../../data/soulsense.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in {db_path}:")
    for table in tables:
        print(f" - {table[0]}")
    conn.close()
else:
    print(f"File not found: {db_path}")
