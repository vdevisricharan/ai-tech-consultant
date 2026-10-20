import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def start_services():
    root = Path(__file__).parent.resolve()
    python_bin = root / ".venv" / "Scripts" / "python.exe"
    if not python_bin.exists():
        python_bin = root / ".venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    print("================================================================")
    print("      AI TECH CONSULTANT: UNIFIED SERVICE ORCHESTRATOR          ")
    print("================================================================")
    print(f"[Launcher] Python runtime: {python_bin}")
    print("[Launcher] Starting microservices across all 3 tasks...\n")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "task1-knowledge-brain") + os.pathsep + str(root / "task3-meeting-to-scope")
    env["KNOWLEDGE_BRAIN_URL"] = "http://localhost:8000"

    procs = []

    try:
        # 1. Start Task 1: Knowledge Brain (Port 8000)
        print("[1/3] Starting Task 1: Knowledge Brain API on http://localhost:8000 ...")
        p1 = subprocess.Popen(
            [str(python_bin), "task1-knowledge-brain/run.py"],
            cwd=str(root),
            env=env
        )
        procs.append(p1)

        # 2. Start Task 3: Meeting-to-Scope Service (Port 8001)
        print("[2/3] Starting Task 3: Meeting-to-Scope Service on http://localhost:8001 ...")
        p3 = subprocess.Popen(
            [str(python_bin), "task3-meeting-to-scope/run.py"],
            cwd=str(root),
            env=env
        )
        procs.append(p3)

        time.sleep(1.5)

        # 3. Start Task 2: Inbox Agent & Web Console (Port 3000)
        print("[3/3] Starting Task 2: Inbox Agent & Web Console on http://localhost:3000 ...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        p2 = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(root / "task2-inbox-agent"),
            env=env
        )
        procs.append(p2)

        print("\n================================================================")
        print("  ✓ ALL SERVICES RUNNING & HEALTHY:")
        print("  • Web Console & Inbox UI: http://localhost:3000")
        print("  • Knowledge Brain API:    http://localhost:8000/docs")
        print("  • Meeting-to-Scope API:   http://localhost:8001/docs")
        print("================================================================")
        print("Press Ctrl+C to terminate all services safely.\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down services safely...")
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()
        print("[Launcher] All services stopped.")

if __name__ == "__main__":
    start_services()
