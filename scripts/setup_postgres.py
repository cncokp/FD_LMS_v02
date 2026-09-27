"""
FD-LMS: Local PostgreSQL Cluster Setup & Schema Migration
Initializes portable PostgreSQL, creates fd_lms database, applies schema.sql,
and populates administrative hierarchy (Divisions > Ranges > Beats).
"""

import os
import sys
import subprocess
import time
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PG_DIR = os.path.join(BASE_DIR, "pgsql")
PG_BIN = os.path.join(PG_DIR, "bin")
PG_DATA = os.path.join(BASE_DIR, "data", "pgdata")
PG_LOG = os.path.join(BASE_DIR, "data", "pg.log")
PG_PORT = int(os.getenv("LOCAL_PG_PORT", 5433))
DB_NAME = "fd_lms"

def run_cmd(cmd, check=True):
    print(f"[CMD] {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(f"[ERR] {res.stderr.strip()}")
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed with code {res.returncode}")
    return res

def is_pg_running():
    pg_ctl = os.path.join(PG_BIN, "pg_ctl.exe")
    res = subprocess.run([pg_ctl, "-D", PG_DATA, "status"], capture_output=True, text=True)
    return res.returncode == 0

def main():
    initdb = os.path.join(PG_BIN, "initdb.exe")
    pg_ctl = os.path.join(PG_BIN, "pg_ctl.exe")
    createdb = os.path.join(PG_BIN, "createdb.exe")
    psql = os.path.join(PG_BIN, "psql.exe")

    if not os.path.exists(initdb):
        print(f"[ERROR] initdb.exe not found at {initdb}")
        sys.exit(1)

    # 1. Initialize DB cluster if not exists
    if not os.path.exists(os.path.join(PG_DATA, "PG_VERSION")):
        print(f"\n--- Initializing Local PostgreSQL Cluster at {PG_DATA} ---")
        os.makedirs(PG_DATA, exist_ok=True)
        run_cmd([initdb, "-D", PG_DATA, "-U", "postgres", "-A", "trust", "-E", "UTF8"])
    else:
        print(f"[OK] Database cluster already initialized at: {PG_DATA}")

    # 2. Start PostgreSQL server
    if not is_pg_running():
        print(f"\n--- Starting Local PostgreSQL Server on port {PG_PORT} ---")
        subprocess.run(
            [pg_ctl, "-D", PG_DATA, "-l", PG_LOG, "-o", f"-p {PG_PORT}", "start"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        # Wait up to 10 seconds for it to become ready
        for _ in range(10):
            time.sleep(1)
            if is_pg_running():
                break
        print(f"[OK] Local PostgreSQL server started on port {PG_PORT}")
    else:
        print(f"[OK] Local PostgreSQL server is already running on port {PG_PORT}")

    # 3. Create fd_lms database if needed
    print(f"\n--- Checking database '{DB_NAME}' ---")
    res_list = run_cmd([psql, "-p", str(PG_PORT), "-U", "postgres", "-lqt"], check=False)
    if DB_NAME not in res_list.stdout:
        print(f"Creating database {DB_NAME}...")
        run_cmd([createdb, "-p", str(PG_PORT), "-U", "postgres", DB_NAME])
    else:
        print(f"[OK] Database '{DB_NAME}' exists.")

    # 4. Apply schema.sql
    schema_path = os.path.join(BASE_DIR, "server", "schema.sql")
    if os.path.exists(schema_path):
        print(f"\n--- Applying Schema from {schema_path} ---")
        run_cmd([psql, "-p", str(PG_PORT), "-U", "postgres", "-d", DB_NAME, "-f", schema_path])

    # 5. Populate Administrative Boundaries (Division, Ranges, Beats)
    print(f"\n--- Seeding Administrative Hierarchy & Boundaries ---")
    import psycopg2
    from psycopg2.extras import Json

    conn = psycopg2.connect(host="127.0.0.1", port=PG_PORT, user="postgres", dbname=DB_NAME)
    cur = conn.cursor()

    # Division
    div_file = os.path.join(BASE_DIR, "static", "data", "division_boundary.geojson")
    if os.path.exists(div_file):
        with open(div_file, "r", encoding="utf-8") as f:
            div_data = json.load(f)
            feat = div_data["features"][0]
            p = feat.get("properties", {})
            cur.execute("""
                INSERT INTO divisions (name, bengali_name, area_name, bengali_area_name, area_acre, bounds, center, geojson)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    area_acre = EXCLUDED.area_acre,
                    bounds = EXCLUDED.bounds,
                    geojson = EXCLUDED.geojson;
            """, (
                p.get("division_name", "Biodiversity Conservation Division"),
                "বন্যপ্রাণী ও প্রকৃতি সংরক্ষণ বিভাগ",
                p.get("area_name", "Bhawal National Park"),
                "ভাওয়াল জাতীয় উদ্যান",
                p.get("area_acre", 24718.23),
                Json(p.get("bounds", [90.349777, 24.036167, 90.468268, 24.181344])),
                Json(p.get("center", [90.409022, 24.108755])),
                Json(feat.get("geometry"))
            ))
        print("  [OK] Division boundary seeded.")

    # Ranges
    range_file = os.path.join(BASE_DIR, "static", "data", "range_boundaries.geojson")
    if os.path.exists(range_file):
        with open(range_file, "r", encoding="utf-8") as f:
            range_data = json.load(f)
            for feat in range_data.get("features", []):
                p = feat.get("properties", {})
                rname = p.get("range_name")
                cur.execute("""
                    INSERT INTO ranges (division_name, name, raw_name, area_acre, bounds, center, geojson)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        area_acre = EXCLUDED.area_acre,
                        bounds = EXCLUDED.bounds,
                        geojson = EXCLUDED.geojson;
                """, (
                    "Biodiversity Conservation Division",
                    rname,
                    p.get("raw_name", rname.replace(" Range", "")),
                    p.get("area_acre", 0.0),
                    Json(p.get("bounds")),
                    Json(p.get("center")),
                    Json(feat.get("geometry"))
                ))
        print("  [OK] Range boundaries seeded.")

    # Beats
    beat_file = os.path.join(BASE_DIR, "static", "data", "beat_boundaries.geojson")
    if os.path.exists(beat_file):
        with open(beat_file, "r", encoding="utf-8") as f:
            beat_data = json.load(f)
            for feat in beat_data.get("features", []):
                p = feat.get("properties", {})
                bname = p.get("beat_name")
                rname = "National Park Range" if bname in ["Park Beat", "Bankhoira Beat", "Baupara Beat"] else "Bhawal Range"
                cur.execute("""
                    INSERT INTO beats (range_name, division_name, name, raw_name, area_acre, center_lat, center_lng, bounds, geojson)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        area_acre = EXCLUDED.area_acre,
                        bounds = EXCLUDED.bounds,
                        geojson = EXCLUDED.geojson;
                """, (
                    rname,
                    "Biodiversity Conservation Division",
                    bname,
                    p.get("raw_name", bname.replace(" Beat", "")),
                    p.get("area_acre", 0.0),
                    p.get("center_lat"),
                    p.get("center_lng"),
                    Json(p.get("bounds")),
                    Json(feat.get("geometry"))
                ))
        print("  [OK] Beat boundaries seeded.")

    conn.commit()
    cur.close()
    conn.close()

    print("\n=======================================================")
    print(f"  LOCAL POSTGRESQL ENVIRONMENT CONFIGURED & READY!    ")
    print(f"  Connection URL: postgresql://postgres@127.0.0.1:{PG_PORT}/{DB_NAME} ")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
