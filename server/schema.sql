-- ==============================================================================
-- FD-LMS: Forest Department Land & Cadastral Management System
-- Enterprise PostgreSQL Database Schema
-- Scalable for Nationwide Deployment (Division > Range > Beat > Mouza > Plots)
-- ==============================================================================

-- 1. Administrative Hierarchy Tables
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS divisions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    bengali_name VARCHAR(200),
    area_name VARCHAR(150),
    bengali_area_name VARCHAR(200),
    area_acre NUMERIC(12, 2) DEFAULT 0.0,
    bounds JSONB,
    center JSONB,
    geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ranges (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES divisions(id) ON DELETE CASCADE,
    division_name VARCHAR(150) DEFAULT 'Biodiversity Conservation Division',
    name VARCHAR(150) NOT NULL UNIQUE,
    raw_name VARCHAR(150),
    bengali_name VARCHAR(200),
    area_acre NUMERIC(12, 2) DEFAULT 0.0,
    bounds JSONB,
    center JSONB,
    geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS beats (
    id SERIAL PRIMARY KEY,
    range_id INTEGER REFERENCES ranges(id) ON DELETE CASCADE,
    range_name VARCHAR(150) NOT NULL,
    division_name VARCHAR(150) DEFAULT 'Biodiversity Conservation Division',
    name VARCHAR(150) NOT NULL UNIQUE,
    raw_name VARCHAR(150),
    bengali_name VARCHAR(200),
    area_acre NUMERIC(12, 2) DEFAULT 0.0,
    center_lat NUMERIC(10, 6),
    center_lng NUMERIC(10, 6),
    bounds JSONB,
    geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mouza_boundaries (
    id SERIAL PRIMARY KEY,
    mouza_name VARCHAR(150) NOT NULL,
    jl_no VARCHAR(50),
    beat_name VARCHAR(150),
    range_name VARCHAR(150),
    division_name VARCHAR(150),
    area_acre NUMERIC(12, 2),
    bounds JSONB,
    geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Spatial Cadastral Plots (CS & RS Surveys)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cs_plots (
    id SERIAL PRIMARY KEY,
    uid VARCHAR(50) UNIQUE,
    plot_no VARCHAR(50) NOT NULL,
    mouza VARCHAR(150) NOT NULL,
    jl_no VARCHAR(50),
    beat_name VARCHAR(150),
    range_name VARCHAR(150),
    division_name VARCHAR(150),
    area_acre NUMERIC(12, 4),
    label_lat NUMERIC(10, 6),
    label_lng NUMERIC(10, 6),
    label_radius NUMERIC(8, 2),
    minx NUMERIC(10, 6),
    miny NUMERIC(10, 6),
    maxx NUMERIC(10, 6),
    maxy NUMERIC(10, 6),
    geometry JSONB,
    geojson JSONB,
    properties JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rs_plots (
    id SERIAL PRIMARY KEY,
    uid VARCHAR(50),
    rs_uid VARCHAR(50) UNIQUE,
    uid2 VARCHAR(50),
    plot_no VARCHAR(50) NOT NULL,
    mouza VARCHAR(150) NOT NULL,
    jl_no VARCHAR(50),
    beat_name VARCHAR(150),
    range_name VARCHAR(150),
    division_name VARCHAR(150),
    area_acre NUMERIC(12, 4),
    label_lat NUMERIC(10, 6),
    label_lng NUMERIC(10, 6),
    label_radius NUMERIC(8, 2),
    minx NUMERIC(10, 6),
    miny NUMERIC(10, 6),
    maxx NUMERIC(10, 6),
    maxy NUMERIC(10, 6),
    geometry JSONB,
    geojson JSONB,
    properties JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabular Dossier & Encroachment Records
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parcel_info (
    id SERIAL PRIMARY KEY,
    cs_uid VARCHAR(50),
    rs_uid VARCHAR(50),
    range VARCHAR(150),
    beat_name VARCHAR(150),
    mouza VARCHAR(150),
    cs_jl VARCHAR(50),
    rs_jl VARCHAR(50),
    cs_plot_no VARCHAR(50),
    rs_plot_no VARCHAR(50),
    cs_land_acre NUMERIC(12, 4),
    total_area NUMERIC(12, 4),
    area_fd NUMERIC(12, 4),
    area_others NUMERIC(12, 4),
    khatian_no VARCHAR(100),
    legal_status VARCHAR(150),
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS encroachment_info (
    id SERIAL PRIMARY KEY,
    uid VARCHAR(50),
    cs_uid VARCHAR(50),
    rs_uid VARCHAR(50),
    district VARCHAR(100) DEFAULT 'Gazipur',
    upazila VARCHAR(100) DEFAULT 'Gazipur Sadar',
    range VARCHAR(150),
    beat_name VARCHAR(150),
    mouza VARCHAR(150),
    cs_plot_no VARCHAR(50),
    rs_plot_no VARCHAR(50),
    rs_khatian VARCHAR(100),
    encroacher_name VARCHAR(250),
    sec_20 VARCHAR(100),
    sec_6 VARCHAR(100),
    encroached_area_acre NUMERIC(12, 4),
    structure_type VARCHAR(150),
    action_taken TEXT,
    geometry JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS boundary_pillars (
    id SERIAL PRIMARY KEY,
    pillar_no VARCHAR(50) NOT NULL,
    division_name VARCHAR(150),
    range_name VARCHAR(150),
    beat_name VARCHAR(150),
    lat NUMERIC(10, 6),
    lng NUMERIC(10, 6),
    status VARCHAR(50) DEFAULT 'Intact',
    survey_date DATE,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. High-Performance B-Tree & Spatial Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cs_plots_plot_no ON cs_plots(plot_no);
CREATE INDEX IF NOT EXISTS idx_cs_plots_uid ON cs_plots(uid);
CREATE INDEX IF NOT EXISTS idx_cs_plots_beat ON cs_plots(beat_name);
CREATE INDEX IF NOT EXISTS idx_cs_plots_mouza ON cs_plots(mouza);
CREATE INDEX IF NOT EXISTS idx_cs_plots_bbox ON cs_plots(minx, miny, maxx, maxy);

CREATE INDEX IF NOT EXISTS idx_rs_plots_plot_no ON rs_plots(plot_no);
CREATE INDEX IF NOT EXISTS idx_rs_plots_rs_uid ON rs_plots(rs_uid);
CREATE INDEX IF NOT EXISTS idx_rs_plots_uid ON rs_plots(uid);
CREATE INDEX IF NOT EXISTS idx_rs_plots_beat ON rs_plots(beat_name);
CREATE INDEX IF NOT EXISTS idx_rs_plots_mouza ON rs_plots(mouza);
CREATE INDEX IF NOT EXISTS idx_rs_plots_bbox ON rs_plots(minx, miny, maxx, maxy);

CREATE INDEX IF NOT EXISTS idx_parcel_info_cs_uid ON parcel_info(cs_uid);
CREATE INDEX IF NOT EXISTS idx_parcel_info_rs_uid ON parcel_info(rs_uid);
CREATE INDEX IF NOT EXISTS idx_parcel_info_beat ON parcel_info(beat_name);

CREATE INDEX IF NOT EXISTS idx_encroach_uid ON encroachment_info(uid);
CREATE INDEX IF NOT EXISTS idx_encroach_cs_uid ON encroachment_info(cs_uid);
CREATE INDEX IF NOT EXISTS idx_encroach_rs_uid ON encroachment_info(rs_uid);
CREATE INDEX IF NOT EXISTS idx_encroach_beat ON encroachment_info(beat_name);

-- 5. User Management & Role-Based Access Control (RBAC)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    role_title VARCHAR(150),
    division VARCHAR(150) DEFAULT 'Biodiversity Conservation Division',
    assigned_range VARCHAR(150),
    assigned_beat VARCHAR(150),
    can_upload BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
