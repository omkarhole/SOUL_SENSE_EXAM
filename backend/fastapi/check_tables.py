import sqlite3

for db in ["data/soulsense.db", "data/soulsense_replica.db"]:
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"{db}: token_revocations present = {'token_revocations' in tables}")
        conn.close()
    except Exception as e:
        print(f"Error reading {db}: {e}")
