-- ============================================================================
-- OrbitGuard Spatial Database Migration Script (PostgreSQL + PostGIS)
-- ============================================================================

-- 1. Enable the PostGIS spatial database extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Create satellites table
CREATE TABLE IF NOT EXISTS satellites (
    norad_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    operator VARCHAR(100),
    type VARCHAR(50),
    tle1 VARCHAR(100) NOT NULL,
    tle2 VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- 3. Create state_vectors table (3D ECI position and velocity coordinates)
CREATE TABLE IF NOT EXISTS state_vectors (
    id SERIAL PRIMARY KEY,
    norad_id INTEGER NOT NULL REFERENCES satellites(norad_id) ON DELETE CASCADE,
    epoch TIMESTAMP NOT NULL,
    position_x DOUBLE PRECISION NOT NULL,
    position_y DOUBLE PRECISION NOT NULL,
    position_z DOUBLE PRECISION NOT NULL,
    velocity_x DOUBLE PRECISION NOT NULL,
    velocity_y DOUBLE PRECISION NOT NULL,
    velocity_z DOUBLE PRECISION NOT NULL
);

-- 4. Create conjunction_events table
CREATE TABLE IF NOT EXISTS conjunction_events (
    id SERIAL PRIMARY KEY,
    primary_norad INTEGER NOT NULL REFERENCES satellites(norad_id) ON DELETE CASCADE,
    secondary_norad INTEGER NOT NULL REFERENCES satellites(norad_id) ON DELETE CASCADE,
    tca TIMESTAMP NOT NULL,
    miss_distance DOUBLE PRECISION NOT NULL,
    radial DOUBLE PRECISION,
    in_track DOUBLE PRECISION,
    cross_track DOUBLE PRECISION,
    pc DOUBLE PRECISION NOT NULL,
    covariance_matrix JSONB,
    compliance_status VARCHAR(50)
);

-- 5. Create reentry_alerts table
CREATE TABLE IF NOT EXISTS reentry_alerts (
    norad_id INTEGER PRIMARY KEY REFERENCES satellites(norad_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    current_altitude DOUBLE PRECISION NOT NULL,
    decay_rate DOUBLE PRECISION,
    eta TIMESTAMP,
    uncertainty_hours DOUBLE PRECISION,
    survival_pct DOUBLE PRECISION,
    corridor_geom GEOMETRY(Polygon, 4326),
    casualty_probability DOUBLE PRECISION
);

-- Create spatial index for corridor_geom to accelerate containment/intersection queries
CREATE INDEX IF NOT EXISTS idx_reentry_alerts_corridor_geom ON reentry_alerts USING GIST(corridor_geom);

-- 6. Create compliance_filings table
CREATE TABLE IF NOT EXISTS compliance_filings (
    id SERIAL PRIMARY KEY,
    operator VARCHAR(100) NOT NULL,
    satellite VARCHAR(100) NOT NULL,
    tca TIMESTAMP NOT NULL,
    form_data JSONB,
    pdf_path VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMP NOT NULL
);
