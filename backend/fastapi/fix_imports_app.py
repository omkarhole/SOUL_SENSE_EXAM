import os

files = [
    r"api/routers/contact.py",
    r"api/routers/deep_dive.py",
    r"api/routers/exams.py",
    r"api/routers/profiles.py",
    r"api/routers/settings_sync.py",
    r"api/routers/tasks.py",
    r"api/routers/questions.py",
    r"api/routers/users.py",
    r"api/routers/export.py",
    r"api/routers/auth.py",
    r"api/routers/assessments.py",
    r"api/routers/analytics.py"
]

base_dir = r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\backend\fastapi"

for rel_path in files:
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content.replace("from ...app", "from app")
        
        if new_content != content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"[FIXED] {rel_path}")
        else:
            print(f"[SKIP] {rel_path} (No change needed or already fixed)")
    else:
        print(f"[ERR] {rel_path} NOT FOUND")
