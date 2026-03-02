import os
import re

FOLDERS = [
    r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\backend\fastapi\api\routers",
    r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\backend\fastapi\api\services",
    r"c:\Users\ayaan shaikh\Documents\EWOC\SOULSENSE2\backend\fastapi\api\models"
]

def fix_imports():
    for folder in FOLDERS:
        if not os.path.exists(folder): continue
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = content
                
                # Fix backend.fastapi.app.core -> ...app.core (depth 3 for routers/services/models relative to root?)
                # Wait, backend/fastapi/api/services/journal_service.py.
                # Relative to journal_service.py: .. is api, ... is fastapi.
                # So ...app.core is correct for all these subfolders of api.
                
                new_content = re.sub(r"from backend\.fastapi\.app\.core", r"from ...app.core", new_content)
                new_content = re.sub(r"from \.\.app\.core", r"from ...app.core", new_content)
                
                # Ensure logging is imported if used
                if ("logging." in new_content or "logger." in new_content) and "import logging" not in new_content:
                    new_content = "import logging\n" + new_content
                
                # Ensure logger is defined if logger. is used
                if "logger." in new_content and "logger =" not in new_content:
                    lines = new_content.split("\n")
                    last_import_line = -1
                    for i, line in enumerate(lines):
                        if line.startswith("import ") or line.startswith("from "):
                            last_import_line = i
                    
                    if last_import_line != -1:
                        lines.insert(last_import_line + 1, "\nlogger = logging.getLogger(__name__)")
                        new_content = "\n".join(lines)
                    else:
                        new_content = "logger = logging.getLogger(__name__)\n" + new_content

                if new_content != content:
                    print(f"Fixing {filename} in {os.path.basename(folder)}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)

if __name__ == "__main__":
    fix_imports()
