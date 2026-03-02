import os
import re

base_dir = r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\backend\fastapi\api"

pattern = re.compile(r"backend\.fastapi\.api")

for root, dirs, files in os.walk(base_dir):
    for name in files:
        if name.endswith(".py"):
            full_path = os.path.join(root, name)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = pattern.sub("api", content)
            
            if new_content != content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[FIXED] {os.path.relpath(full_path, base_dir)}")
