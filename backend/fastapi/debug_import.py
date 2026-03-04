import sys
import os
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    print("Attempting to import api.main...")
    import api.main
    print("Import successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
