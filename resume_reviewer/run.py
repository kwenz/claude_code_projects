#!/usr/bin/env python3
"""
Start the Resume Reviewer backend and frontend together.
Usage: python run.py
"""

import os
import subprocess
import sys
import time
import signal
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

# Detect venv python
if sys.platform == "win32":
    VENV_PYTHON = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(BACKEND_DIR, "venv", "bin", "python")

VENV_SITE_PACKAGES = os.path.join(
    BACKEND_DIR, "venv", "lib",
    f"python{sys.version_info.major}.{sys.version_info.minor}",
    "site-packages",
)

processes = []


def check_env():
    env_file = os.path.join(BACKEND_DIR, ".env")
    if not os.path.exists(env_file):
        print(f"[error] backend/.env not found — copy .env.example and add your API keys.")
        sys.exit(1)
    if not os.path.exists(VENV_PYTHON):
        print(f"[error] Venv not found at {VENV_PYTHON}")
        print("  Run: cd backend && python -m venv venv && venv/bin/pip install -r requirements.txt")
        sys.exit(1)
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print("[info] node_modules not found — installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)


def wait_for_backend(timeout=30):
    url = "http://localhost:8000/api/health"
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def shutdown(signum=None, frame=None):
    print("\n[run.py] Shutting down...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=5)
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def main():
    check_env()

    env = os.environ.copy()
    env["PYTHONPATH"] = VENV_SITE_PACKAGES

    print("[run.py] Starting backend on http://localhost:8000 ...")
    backend = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=env,
    )
    processes.append(backend)

    if not wait_for_backend():
        print("[error] Backend failed to start. Check the output above.")
        shutdown()

    print("[run.py] Starting frontend on http://localhost:5173 ...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
    )
    processes.append(frontend)

    print("\n  Backend:  http://localhost:8000")
    print("  Frontend: http://localhost:5173")
    print("\n  Press Ctrl+C to stop.\n")

    try:
        while True:
            if backend.poll() is not None:
                print("[error] Backend exited unexpectedly.")
                shutdown()
            if frontend.poll() is not None:
                print("[error] Frontend exited unexpectedly.")
                shutdown()
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
