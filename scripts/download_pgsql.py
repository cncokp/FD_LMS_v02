import os
import sys
import time
import urllib.request
import zipfile

ZIP_URL = "https://get.enterprisedb.com/postgresql/postgresql-16.15-4-windows-x64-binaries.zip"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_DIR = os.path.join(BASE_DIR, "pgsql")
ZIP_PATH = os.path.join(BASE_DIR, "data", "postgresql-16-binaries.zip")

def main():
    if os.path.exists(os.path.join(DEST_DIR, "bin", "postgres.exe")):
        print(f"[OK] PostgreSQL binaries already exist at: {DEST_DIR}")
        return

    os.makedirs(os.path.dirname(ZIP_PATH), exist_ok=True)
    
    print(f"[FD-LMS] Downloading PostgreSQL 16 portable binaries from EDB...")
    req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req) as resp, open(ZIP_PATH, "wb") as out_file:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 1024 * 1024  # 1 MB
        t0 = time.time()
        last_print = 0

        while True:
            chunk = resp.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_print >= 3.0 or downloaded == total_size:
                last_print = now
                mb_down = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                pct = (downloaded / total_size * 100) if total_size else 0
                speed = mb_down / (now - t0) if (now - t0) > 0 else 0
                print(f"[FD-LMS Download] {mb_down:.1f}/{mb_total:.1f} MB ({pct:.1f}%) - Speed: {speed:.2f} MB/s", flush=True)

    print(f"\n[FD-LMS] Download complete ({os.path.getsize(ZIP_PATH):,} bytes). Extracting...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        zf.extractall(BASE_DIR)
    
    try:
        os.remove(ZIP_PATH)
    except OSError:
        pass

    bin_path = os.path.join(DEST_DIR, "bin", "postgres.exe")
    if os.path.exists(bin_path):
        print(f"[SUCCESS] PostgreSQL 16 portable binaries installed at: {DEST_DIR}")
    else:
        print(f"[WARNING] Extraction finished, checking contents of {DEST_DIR}...")

if __name__ == "__main__":
    main()
