"""
FD-LMS Administrative Hierarchy Module
Manages Division > Range > Beat administrative structure, spatial boundaries, and metrics.
Hierarchy:
  Biodiversity Conservation Division
    └── Bhawal National Park
        ├── National Park Range (3 Beats: Park, Bankhoira, Baupara)
        └── Bhawal Range (4 Beats: BK Bari, Rajendrapur West, Baruipara, Bhabanipur)
"""

import os
import json
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DATA_DIR = os.path.join(BASE_DIR, "static", "data")

BEAT_TO_RANGE = {
    "Park Beat": "National Park Range",
    "Bankhoira Beat": "National Park Range",
    "Baupara Beat": "National Park Range",
    "BK Bari Beat": "Bhawal Range",
    "Rajendrapur West Beat": "Bhawal Range",
    "Baruipara Beat": "Bhawal Range",
    "Bhabanipur Beat": "Bhawal Range"
}

RANGE_BEATS = {
    "National Park Range": ["Park Beat", "Bankhoira Beat", "Baupara Beat"],
    "Bhawal Range": ["BK Bari Beat", "Rajendrapur West Beat", "Baruipara Beat", "Bhabanipur Beat"]
}

_division_cache = None
_ranges_cache = None
_beats_cache = None

def get_division_geojson() -> Dict[str, Any]:
    global _division_cache
    if _division_cache is not None:
        return _division_cache
    path = os.path.join(STATIC_DATA_DIR, "division_boundary.geojson")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _division_cache = json.load(f)
            return _division_cache
    return {"type": "FeatureCollection", "features": []}

def get_ranges_geojson() -> Dict[str, Any]:
    global _ranges_cache
    if _ranges_cache is not None:
        return _ranges_cache
    path = os.path.join(STATIC_DATA_DIR, "range_boundaries.geojson")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _ranges_cache = json.load(f)
            return _ranges_cache
    return {"type": "FeatureCollection", "features": []}

def get_beats_geojson() -> Dict[str, Any]:
    global _beats_cache
    if _beats_cache is not None:
        return _beats_cache
    path = os.path.join(STATIC_DATA_DIR, "beat_boundaries.geojson")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _beats_cache = json.load(f)
            # Inject range info if missing
            for feat in _beats_cache.get("features", []):
                p = feat.setdefault("properties", {})
                bname = p.get("beat_name") or p.get("name")
                if bname in BEAT_TO_RANGE:
                    p["range_name"] = BEAT_TO_RANGE[bname]
                    p["range"] = BEAT_TO_RANGE[bname]
            return _beats_cache
    return {"type": "FeatureCollection", "features": []}

def get_hierarchy_tree() -> Dict[str, Any]:
    """
    Returns full hierarchy tree with live administrative metadata and counts.
    """
    beats_fc = get_beats_geojson()
    beat_props = {}
    for f in beats_fc.get("features", []):
        p = f.get("properties", {})
        bname = p.get("beat_name") or p.get("name")
        if bname:
            beat_props[bname] = p

    ranges = []
    for rname, bnames in RANGE_BEATS.items():
        child_beats = []
        range_acres = 0.0
        for b in bnames:
            bp = beat_props.get(b, {})
            acres = float(bp.get("area_acre", 0.0))
            range_acres += acres
            child_beats.append({
                "id": bp.get("id"),
                "name": b,
                "range_name": rname,
                "area_acre": round(acres, 2),
                "center_lat": bp.get("center_lat"),
                "center_lng": bp.get("center_lng"),
                "bounds": bp.get("bounds")
            })

        ranges.append({
            "name": rname,
            "raw_name": rname.replace(" Range", ""),
            "area_acre": round(range_acres, 2),
            "beat_count": len(child_beats),
            "beats": child_beats
        })

    total_div_acres = sum(r["area_acre"] for r in ranges)

    div_obj = {
        "name": "Biodiversity Conservation Division",
        "bengali_name": "বন্যপ্রাণী ও প্রকৃতি সংরক্ষণ বিভাগ",
        "area_name": "Bhawal National Park",
        "display_name": "Bhawal National Park",
        "bengali_area_name": "ভাওয়াল জাতীয় উদ্যান",
        "total_acre": round(total_div_acres, 2),
        "area_acre": round(total_div_acres, 2),
        "forest_plots_count": 3518,
        "cadastral_plots_count": 19463,
        "encroachments_count": 41,
        "range_count": len(ranges),
        "beat_count": len(beat_props),
        "ranges": ranges
    }

    return {
        "division": div_obj,
        "name": div_obj["name"],
        "display_name": div_obj["display_name"],
        "area_acre": div_obj["area_acre"],
        "forest_plots_count": 3518,
        "cadastral_plots_count": 19463,
        "encroachments_count": 41,
        "ranges": ranges
    }


try:
    from server import db
except ImportError:
    import db


def get_all_divisions() -> List[Dict[str, Any]]:
    """Return all divisions from database or fallback defaults"""
    divisions = []
    try:
        if db.is_local_pg_enabled():
            with db.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name, bengali_name, area_name, area_acre, created_at FROM divisions ORDER BY id ASC;")
                    rows = cur.fetchall()
                    for r in rows:
                        d = dict(r)
                        if d.get("created_at"):
                            d["created_at"] = str(d["created_at"])
                        divisions.append(d)
    except Exception as e:
        print(f"[HIERARCHY] get_all_divisions DB failed: {e}")

    if not divisions:
        divisions = [{
            "id": 1,
            "name": "Biodiversity Conservation Division",
            "bengali_name": "বন্যপ্রাণী ও প্রকৃতি সংরক্ষণ বিভাগ",
            "area_name": "Bhawal National Park",
            "area_acre": 24718.0
        }]
    return divisions


def get_all_ranges(division_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all ranges, optionally filtered by division"""
    ranges = []
    try:
        if db.is_local_pg_enabled():
            with db.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    if division_name:
                        cur.execute("SELECT id, division_name, name, raw_name, bengali_name, area_acre FROM ranges WHERE division_name = %s ORDER BY id ASC;", (division_name,))
                    else:
                        cur.execute("SELECT id, division_name, name, raw_name, bengali_name, area_acre FROM ranges ORDER BY id ASC;")
                    rows = cur.fetchall()
                    for r in rows:
                        ranges.append(dict(r))
    except Exception as e:
        print(f"[HIERARCHY] get_all_ranges DB failed: {e}")

    if not ranges:
        ranges = [
            {"id": 1, "division_name": "Biodiversity Conservation Division", "name": "National Park Range", "raw_name": "National Park", "area_acre": 10240.0},
            {"id": 2, "division_name": "Biodiversity Conservation Division", "name": "Bhawal Range", "raw_name": "Bhawal", "area_acre": 14478.0}
        ]
    return ranges


def get_all_beats(range_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all beats, optionally filtered by range"""
    beats = []
    try:
        if db.is_local_pg_enabled():
            with db.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    if range_name:
                        cur.execute("SELECT id, range_name, division_name, name, raw_name, bengali_name, area_acre, center_lat, center_lng FROM beats WHERE range_name = %s ORDER BY id ASC;", (range_name,))
                    else:
                        cur.execute("SELECT id, range_name, division_name, name, raw_name, bengali_name, area_acre, center_lat, center_lng FROM beats ORDER BY id ASC;")
                    rows = cur.fetchall()
                    for r in rows:
                        beats.append(dict(r))
    except Exception as e:
        print(f"[HIERARCHY] get_all_beats DB failed: {e}")

    if not beats:
        default_beats = [
            {"id": 1, "range_name": "National Park Range", "name": "Park Beat", "raw_name": "Park", "area_acre": 3450.0},
            {"id": 2, "range_name": "National Park Range", "name": "Bankhoira Beat", "raw_name": "Bankhoira", "area_acre": 3120.0},
            {"id": 3, "range_name": "National Park Range", "name": "Baupara Beat", "raw_name": "Baupara", "area_acre": 3670.0},
            {"id": 4, "range_name": "Bhawal Range", "name": "BK Bari Beat", "raw_name": "BK Bari", "area_acre": 3890.0},
            {"id": 5, "range_name": "Bhawal Range", "name": "Rajendrapur West Beat", "raw_name": "Rajendrapur West", "area_acre": 4120.0},
            {"id": 6, "range_name": "Bhawal Range", "name": "Baruipara Beat", "raw_name": "Baruipara", "area_acre": 3218.0},
            {"id": 7, "range_name": "Bhawal Range", "name": "Bhabanipur Beat", "raw_name": "Bhabanipur", "area_acre": 3250.0}
        ]
        if range_name:
            beats = [b for b in default_beats if b["range_name"].lower() == range_name.lower()]
        else:
            beats = default_beats
    return beats


def create_division(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_name = str(data.get("area_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    if not name:
        raise ValueError("Division name is required")

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO divisions (name, bengali_name, area_name, area_acre)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        bengali_name = EXCLUDED.bengali_name,
                        area_name = EXCLUDED.area_name,
                        area_acre = EXCLUDED.area_acre,
                        updated_at = NOW()
                    RETURNING id, name, bengali_name, area_name, area_acre;
                """, (name, bengali_name, area_name, area_acre))
                row = cur.fetchone()
                conn.commit()
                return dict(row)
    return {"name": name, "bengali_name": bengali_name, "area_acre": area_acre}


def create_range(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    division_name = str(data.get("division_name", "Biodiversity Conservation Division")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    if not name:
        raise ValueError("Range name is required")

    if not name.lower().endswith("range"):
        name = f"{name} Range"
    raw_name = name.replace(" Range", "").strip()

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ranges (name, division_name, raw_name, bengali_name, area_acre)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        division_name = EXCLUDED.division_name,
                        raw_name = EXCLUDED.raw_name,
                        bengali_name = EXCLUDED.bengali_name,
                        area_acre = EXCLUDED.area_acre,
                        updated_at = NOW()
                    RETURNING id, name, division_name, raw_name, bengali_name, area_acre;
                """, (name, division_name, raw_name, bengali_name, area_acre))
                row = cur.fetchone()
                conn.commit()
                return dict(row)
    return {"name": name, "division_name": division_name, "area_acre": area_acre}


def create_beat(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    range_name = str(data.get("range_name", "")).strip()
    division_name = str(data.get("division_name", "Biodiversity Conservation Division")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    center_lat = float(data["center_lat"]) if data.get("center_lat") else None
    center_lng = float(data["center_lng"]) if data.get("center_lng") else None

    if not name or not range_name:
        raise ValueError("Beat name and Range name are required")

    if not name.lower().endswith("beat"):
        name = f"{name} Beat"
    raw_name = name.replace(" Beat", "").strip()

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO beats (name, range_name, division_name, raw_name, bengali_name, area_acre, center_lat, center_lng)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        range_name = EXCLUDED.range_name,
                        division_name = EXCLUDED.division_name,
                        raw_name = EXCLUDED.raw_name,
                        bengali_name = EXCLUDED.bengali_name,
                        area_acre = EXCLUDED.area_acre,
                        center_lat = EXCLUDED.center_lat,
                        center_lng = EXCLUDED.center_lng,
                        updated_at = NOW()
                    RETURNING id, name, range_name, division_name, raw_name, bengali_name, area_acre, center_lat, center_lng;
                """, (name, range_name, division_name, raw_name, bengali_name, area_acre, center_lat, center_lng))
                row = cur.fetchone()
                conn.commit()
                return dict(row)
    return {"name": name, "range_name": range_name, "area_acre": area_acre}


def save_jurisdiction_boundary(level: str, name: str, geojson_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save GeoJSON boundary for division, range, or beat into database"""
    global _division_cache, _ranges_cache, _beats_cache
    _division_cache = None
    _ranges_cache = None
    _beats_cache = None

    lvl = level.strip().lower()
    geojson_str = json.dumps(geojson_data)

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                if lvl == "division":
                    cur.execute("""
                        INSERT INTO divisions (name, geojson)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO UPDATE SET geojson = EXCLUDED.geojson, updated_at = NOW();
                    """, (name, geojson_str))
                elif lvl == "range":
                    cur.execute("""
                        INSERT INTO ranges (name, geojson)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO UPDATE SET geojson = EXCLUDED.geojson, updated_at = NOW();
                    """, (name, geojson_str))
                elif lvl == "beat":
                    cur.execute("""
                        INSERT INTO beats (name, geojson)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO UPDATE SET geojson = EXCLUDED.geojson, updated_at = NOW();
                    """, (name, geojson_str))
                conn.commit()

    return {"status": "success", "level": lvl, "name": name, "features_saved": len(geojson_data.get("features", []))}


def update_division(division_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_name = str(data.get("area_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    if not name:
        raise ValueError("Division name cannot be empty")

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM divisions WHERE id = %s;", (division_id,))
                old_row = cur.fetchone()
                if not old_row:
                    raise ValueError(f"Division with ID {division_id} not found")
                old_name = old_row["name"]

                cur.execute("""
                    UPDATE divisions
                    SET name = %s, bengali_name = %s, area_name = %s, area_acre = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, bengali_name, area_name, area_acre;
                """, (name, bengali_name, area_name, area_acre, division_id))
                row = cur.fetchone()

                if old_name != name:
                    cur.execute("UPDATE ranges SET division_name = %s WHERE division_name = %s;", (name, old_name))
                    cur.execute("UPDATE beats SET division_name = %s WHERE division_name = %s;", (name, old_name))

                conn.commit()
                return dict(row)
    return {"id": division_id, "name": name, "bengali_name": bengali_name, "area_acre": area_acre}


def delete_division(division_id: int) -> bool:
    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM divisions WHERE id = %s;", (division_id,))
                row = cur.fetchone()
                if not row:
                    return False
                div_name = row["name"]
                cur.execute("DELETE FROM beats WHERE division_name = %s;", (div_name,))
                cur.execute("DELETE FROM ranges WHERE division_name = %s;", (div_name,))
                cur.execute("DELETE FROM divisions WHERE id = %s;", (division_id,))
                conn.commit()
                return True
    return True


def update_range(range_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    division_name = str(data.get("division_name", "Biodiversity Conservation Division")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    if not name:
        raise ValueError("Range name cannot be empty")

    if not name.lower().endswith("range"):
        name = f"{name} Range"
    raw_name = name.replace(" Range", "").strip()

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, division_name FROM ranges WHERE id = %s;", (range_id,))
                old_row = cur.fetchone()
                if not old_row:
                    raise ValueError(f"Range with ID {range_id} not found")
                old_name = old_row["name"]

                cur.execute("""
                    UPDATE ranges
                    SET name = %s, division_name = %s, raw_name = %s, bengali_name = %s, area_acre = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, division_name, raw_name, bengali_name, area_acre;
                """, (name, division_name, raw_name, bengali_name, area_acre, range_id))
                row = cur.fetchone()

                cur.execute("""
                    UPDATE beats 
                    SET range_name = %s, division_name = %s 
                    WHERE range_name = %s;
                """, (name, division_name, old_name))

                conn.commit()
                return dict(row)
    return {"id": range_id, "name": name, "division_name": division_name, "area_acre": area_acre}


def delete_range(range_id: int) -> bool:
    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM ranges WHERE id = %s;", (range_id,))
                row = cur.fetchone()
                if not row:
                    return False
                range_name = row["name"]
                cur.execute("DELETE FROM beats WHERE range_name = %s;", (range_name,))
                cur.execute("DELETE FROM ranges WHERE id = %s;", (range_id,))
                conn.commit()
                return True
    return True


def update_beat(beat_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", "")).strip()
    range_name = str(data.get("range_name", "")).strip()
    division_name = str(data.get("division_name", "")).strip()
    bengali_name = str(data.get("bengali_name", "")).strip()
    area_acre = float(data.get("area_acre", 0.0) or 0.0)
    center_lat = float(data["center_lat"]) if data.get("center_lat") is not None and str(data.get("center_lat")).strip() != "" else None
    center_lng = float(data["center_lng"]) if data.get("center_lng") is not None and str(data.get("center_lng")).strip() != "" else None

    if not name or not range_name:
        raise ValueError("Beat name and Range name are required")

    if not name.lower().endswith("beat"):
        name = f"{name} Beat"
    raw_name = name.replace(" Beat", "").strip()

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                if not division_name:
                    cur.execute("SELECT division_name FROM ranges WHERE name = %s;", (range_name,))
                    r_row = cur.fetchone()
                    division_name = r_row["division_name"] if r_row else "Biodiversity Conservation Division"

                cur.execute("""
                    UPDATE beats
                    SET name = %s, range_name = %s, division_name = %s, raw_name = %s,
                        bengali_name = %s, area_acre = %s, center_lat = %s, center_lng = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, range_name, division_name, raw_name, bengali_name, area_acre, center_lat, center_lng;
                """, (name, range_name, division_name, raw_name, bengali_name, area_acre, center_lat, center_lng, beat_id))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Beat with ID {beat_id} not found")
                conn.commit()
                return dict(row)
    return {"id": beat_id, "name": name, "range_name": range_name, "area_acre": area_acre}


def delete_beat(beat_id: int) -> bool:
    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM beats WHERE id = %s RETURNING id;", (beat_id,))
                deleted = cur.fetchone()
                conn.commit()
                return bool(deleted)
    return True

