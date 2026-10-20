import sys
from pathlib import Path

# Ensure task directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting Knowledge Brain API on http://{settings.task1_host}:{settings.task1_port}")
    uvicorn.run("app.main:app", host=settings.task1_host, port=settings.task1_port, reload=False)
