import sqlite3
import os

db_path = r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\data\soulsense.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check current columns
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    print(f"Current columns in 'users': {columns}")
    
    to_add = [
        ('is_admin', 'BOOLEAN DEFAULT 0'),
        ('is_2fa_enabled', 'BOOLEAN DEFAULT 0'),
        ('otp_secret', 'TEXT'),
        ('last_activity', 'DATETIME'),
        ('onboarding_completed', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in to_add:
        if col_name not in columns:
            try:
                print(f"Adding column {col_name}...")
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Failed to add {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
