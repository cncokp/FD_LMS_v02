"""
FD-LMS: Forest Department Land Management System Launcher
Local Development Server with live reload and Supabase cloud synchronization.
Single unified backend for local and online verification.
"""

import os
import sys
import webbrowser
import threading
import time

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

import uvicorn

def ensure_local_postgres():
    pg_ctl = os.path.join(BASE_DIR, "pgsql", "bin", "pg_ctl.exe")
    pg_data = os.path.join(BASE_DIR, "data", "pgdata")
    pg_log = os.path.join(BASE_DIR, "data", "pg.log")
    pg_port = int(os.getenv("LOCAL_PG_PORT", 5433))

    if not os.path.exists(pg_ctl) or not os.path.exists(os.path.join(pg_data, "PG_VERSION")):
        print(f"[FD-LMS] WARNING: Local PostgreSQL binaries or cluster not found. Run scripts/setup_postgres.py")
        return False

    import subprocess
    res = subprocess.run([pg_ctl, "-D", pg_data, "status"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FD-LMS] Starting Local PostgreSQL on port {pg_port}...")
        subprocess.run(
            [pg_ctl, "-D", pg_data, "-l", pg_log, "-o", f"-p {pg_port}", "start"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)
        status_res = subprocess.run([pg_ctl, "-D", pg_data, "status"], capture_output=True, text=True)
        if status_res.returncode == 0:
            print(f"[FD-LMS] Local PostgreSQL started successfully on port {pg_port} [OK]")
        else:
            print(f"[FD-LMS] Warning: Failed to start local PostgreSQL on port {pg_port}")
            return False
    else:
        print(f"[FD-LMS] Local PostgreSQL is active on port {pg_port} [OK]")
    return True

def verify_backend():
    from server import db
    if db.is_local_pg_enabled():
        ensure_local_postgres()
        print(f"[FD-LMS] Database Backend : Local PostgreSQL 16 (100% Offline Dev)")
        print(f"[FD-LMS] Connection URL   : {db.LOCAL_DB_URL}")
        print(f"[FD-LMS] Cloud Isolation  : Supabase Cloud preserved for production (not queried in dev)")
        print(f"[FD-LMS] Browser Cache    : Completely DISABLED (no-store, no-cache)")
    elif db.is_supabase_enabled():
        supabase_url = os.getenv("SUPABASE_URL", "https://tbffjjlkmzswcmwdkulh.supabase.co")
        print(f"[FD-LMS] Database Backend : Supabase Cloud (Single Source of Truth)")
        print(f"[FD-LMS] Supabase Endpoint: {supabase_url}")
        print(f"[FD-LMS] Environment Mode : Cloud Connected")
    else:
        print("[FD-LMS] WARNING: No database credentials configured.")

def open_browser(port=8000):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"[FD-LMS] WebGIS Portal is accessible at : {url}")
    print(f"[FD-LMS] Admin Portal is accessible at  : {url}/admin")
    print(f"[FD-LMS] Interactive API Documentation : {url}/docs\n")
    if not os.environ.get("FD_NO_BROWSER"):
        webbrowser.open(url)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    print("\n" + "=" * 65)
    print("      FD-LMS Development Server (Local + Supabase Cloud)")
    print("=" * 65)
    verify_backend()
    print("=" * 65 + "\n")

    # Only open browser once from the master process
    if os.environ.get("UVICORN_RELOAD") != "true" and not os.environ.get("FD_BROWSER_OPENED"):
        os.environ["FD_BROWSER_OPENED"] = "1"
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[os.path.join(BASE_DIR, "server"), os.path.join(BASE_DIR, "static")]
    )
