import sys
from pathlib import Path

# Ensure task directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

if __name__ == "__main__":
    print("Starting Meeting-to-Scope Service on http://0.0.0.0:8001")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=False)
