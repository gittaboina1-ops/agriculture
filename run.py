#!/usr/bin/env python3
"""
AgriGraph Unified Runner
Starts both FastAPI Backend (port 8000) and React Frontend (port 5173).
Press Ctrl+C to gracefully stop both servers.
"""

import os
import sys
import subprocess
import time
import signal
import threading

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

def stream_logs(pipe, prefix):
    """Prints output lines with an identifying server prefix."""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                print(f"[{prefix}] {line.strip()}", flush=True)
    except Exception:
        pass

def main():
    print("=" * 65)
    print("🌱 STARTING AGRIGRAPH MVP (FASTAPI BACKEND + REACT FRONTEND)")
    print("=" * 65)

    # 1. Start FastAPI Backend
    print("--> Starting FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # 2. Start Vite Frontend
    print("--> Starting React Vite Frontend on http://localhost:5173 ...")
    frontend_cmd = ["npm", "run", "dev", "--", "--host"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream logs asynchronously
    threading.Thread(target=stream_logs, args=(backend_proc.stdout, "BACKEND"), daemon=True).start()
    threading.Thread(target=stream_logs, args=(frontend_proc.stdout, "FRONTEND"), daemon=True).start()

    time.sleep(2)
    print("\n" + "=" * 65)
    print("🚀 BOTH SERVERS ARE RUNNING!")
    print("   🌐 Frontend UI:  http://localhost:5173")
    print("   ⚡ Backend API:  http://localhost:8000")
    print("   📖 Swagger Docs: http://localhost:8000/docs")
    print("=" * 65)
    print("Press Ctrl+C at any time to shut down both servers.\n")

    def shutdown(signum=None, frame=None):
        print("\n[!] Shutting down AgriGraph servers...")
        try:
            frontend_proc.terminate()
            backend_proc.terminate()
            frontend_proc.wait(timeout=3)
            backend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()
            backend_proc.kill()
        print("[✓] All servers terminated cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            b_status = backend_proc.poll()
            f_status = frontend_proc.poll()
            if b_status is not None:
                print(f"[!] Backend exited with status {b_status}")
                shutdown()
            if f_status is not None:
                print(f"[!] Frontend exited with status {f_status}")
                shutdown()
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()
