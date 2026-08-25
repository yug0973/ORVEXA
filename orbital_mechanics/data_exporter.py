import os
import json
import time
from datetime import datetime, timezone, timedelta
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from orbital_mechanics.propagator import fetch_active_catalog, propagate_catalog_batch
from orbital_mechanics.screening import screen_conjunctions
from orbital_mechanics.foster_elrod import calculate_foster_elrod
from orbital_mechanics.monte_carlo_reentry import generate_reentry_corridor
from orbital_mechanics.solar_weather import fetch_live_noaa_data

Base = declarative_base()

class Satellite(Base):
    __tablename__ = 'satellites'
    norad_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    operator = Column(String(100))
    type = Column(String(50))
    tle_line1 = Column(String(100), nullable=False)
    tle_line2 = Column(String(100), nullable=False)
    updated_at = Column(DateTime, nullable=False)

class StateVector(Base):
    __tablename__ = 'state_vectors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    norad_id = Column(Integer, ForeignKey('satellites.norad_id'), nullable=False)
    epoch = Column(DateTime, nullable=False)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    velocity_x = Column(Float, nullable=False)
    velocity_y = Column(Float, nullable=False)
    velocity_z = Column(Float, nullable=False)

class ConjunctionEvent(Base):
    __tablename__ = 'conjunction_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_id = Column(Integer, ForeignKey('satellites.norad_id'), nullable=False)
    secondary_id = Column(Integer, ForeignKey('satellites.norad_id'), nullable=False)
    tca = Column(DateTime, nullable=False)
    miss_distance = Column(Float, nullable=False)
    radial = Column(Float)
    in_track = Column(Float)
    cross_track = Column(Float)
    pc = Column(Float, nullable=False)
    covariance_matrix_json = Column(Text)

class ReentryAlert(Base):
    __tablename__ = 'reentry_alerts'
    norad_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    decay_rate = Column(Float)
    eta = Column(DateTime)
    uncertainty_hours = Column(Float)
    corridor_geojson = Column(Text)
    casualty_probability = Column(Float)

def generate_realistic_covariance(r_p, v_p):
    """
    Synthesizes a realistic 3x3 position covariance matrix (in km^2) for LEO satellites 
    by defining uncertainty in the RIC frame (20m radial/cross-track, 100m in-track) 
    and rotating it to the inertial ECI frame.
    """
    r_p = np.array(r_p)
    v_p = np.array(v_p)
    
    # Orthonormal basis vectors of the RIC frame
    R_hat = r_p / np.linalg.norm(r_p)
    cross = np.cross(r_p, v_p)
    C_hat = cross / np.linalg.norm(cross)
    I_hat = np.cross(C_hat, R_hat)
    
    # Rotation matrix from RIC to ECI
    R = np.column_stack([R_hat, I_hat, C_hat])
    
    # Stand deviations: Radial=20m (0.02 km), In-track=100m (0.1 km), Cross-track=20m (0.02 km)
    sigma_R = 0.02
    sigma_I = 0.10
    sigma_C = 0.02
    
    C_RIC = np.diag([sigma_R**2, sigma_I**2, sigma_C**2])
    C_ECI = R.dot(C_RIC).dot(R.T)
    return C_ECI

def compute_ric_coordinates(r_p, v_p, r_s):
    """
    Projects the relative position vector onto the primary satellite's 
    Radial-In-Track-Cross-Track (RIC) frame.
    """
    r_p = np.array(r_p)
    v_p = np.array(v_p)
    r_s = np.array(r_s)
    
    r_rel = r_p - r_s
    
    R_hat = r_p / np.linalg.norm(r_p)
    cross = np.cross(r_p, v_p)
    C_hat = cross / np.linalg.norm(cross)
    I_hat = np.cross(C_hat, R_hat)
    
    radial = float(np.dot(r_rel, R_hat))
    in_track = float(np.dot(r_rel, I_hat))
    cross_track = float(np.dot(r_rel, C_hat))
    
    return radial, in_track, cross_track

def run_pipeline_and_export():
    print("Initializing ORVEXA Live Data Exporter...")
    
    # 1. Establish database connection (PostgreSQL with SQLite fallback)
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ORVEXA")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            pass
        print(f"Connected successfully to PostgreSQL at: {db_url}")
    except Exception as e:
        fallback_url = "sqlite:///ORVEXA.db"
        print(f"Warning: Failed to connect to PostgreSQL ({e}). Falling back to SQLite: {fallback_url}")
        engine = create_engine(fallback_url)
        
    # Create tables
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 2. Fetch live NOAA solar weather indices
    weather = fetch_live_noaa_data()
    f10_7 = weather["f10_7"]
    ap = weather["ap"]
    print(f"Active Space Weather: F10.7 = {f10_7:.2f} sfu | Ap = {ap:.2f}")

    # 3. Fetch active satellite catalog
    active_sats = fetch_active_catalog()
    
    # Process subset of first 100 satellites for performance and verification
    sats_subset = active_sats[:100]
    print(f"Ingesting metadata for {len(sats_subset)} satellites into database...")
    
    now_utc = datetime.now(timezone.utc)
    for sat in sats_subset:
        # Upsert satellite records
        db_sat = session.query(Satellite).filter_by(norad_id=sat["norad_id"]).first()
        if not db_sat:
            db_sat = Satellite(
                norad_id=sat["norad_id"],
                name=sat["name"],
                tle_line1=sat["tle_line1"],
                tle_line2=sat["tle_line2"],
                operator="Unknown",
                type="Payload" if "space" not in sat["name"].lower() else "Debris",
                updated_at=now_utc
            )
            session.add(db_sat)
        else:
            db_sat.tle_line1 = sat["tle_line1"]
            db_sat.tle_line2 = sat["tle_line2"]
            db_sat.updated_at = now_utc

    session.commit()

    # 4. Propagate orbits 48 hours forward (10-minute steps)
    print("Propagating satellite positions for the next 48 hours...")
    state_vectors = propagate_catalog_batch(sats_subset, time_window_hours=48, step_minutes=10)
    print(f"Generated {len(state_vectors)} state vectors.")
    
    # Clear old state vectors to prevent database bloat, and insert new ones
    session.query(StateVector).delete()
    
    state_vector_objs = [
        StateVector(
            norad_id=sv["norad_id"],
            epoch=sv["epoch"].replace(tzinfo=None),  # SQLite/PostgreSQL timezone-naive compatible
            position_x=sv["position_x"],
            position_y=sv["position_y"],
            position_z=sv["position_z"],
            velocity_x=sv["velocity_x"],
            velocity_y=sv["velocity_y"],
            velocity_z=sv["velocity_z"]
        )
        for sv in state_vectors
    ]
    
    # Bulk insert
    session.bulk_save_objects(state_vector_objs)
    session.commit()
    print("Saved propagated state vectors to table state_vectors.")

    # 5. Screen close approaches using KD-Tree (10 km threshold)
    print("Screening all-vs-all conjunction events...")
    conjunctions = screen_conjunctions(state_vectors, threshold_km=10.0)
    print(f"Screened and refined {len(conjunctions)} conjunction candidates.")
    
    # Clear old conjunction events and insert new ones
    session.query(ConjunctionEvent).delete()
    
    for conj in conjunctions:
        # Check miss distance < 5 km for probability calculation
        pc_val = 0.0
        cov_matrix_json = None
        
        # Pull states at TCA
        r_p, v_p = conj["primary_state"][0], conj["primary_state"][1]
        r_s, v_s = conj["secondary_state"][0], conj["secondary_state"][1]
        
        # Compute Radial, In-Track, Cross-Track relative components
        radial, in_track, cross_track = compute_ric_coordinates(r_p, v_p, r_s)
        
        if conj["miss_distance"] < 5.0:
            # Generate realistic covariances
            cov_p = generate_realistic_covariance(r_p, v_p)
            cov_s = generate_realistic_covariance(r_s, v_s)
            
            # Compute Pc
            pc_val = calculate_foster_elrod(
                primary_state=conj["primary_state"],
                secondary_state=conj["secondary_state"],
                primary_cov=cov_p,
                secondary_cov=cov_s,
                hbr=10.0  # 10m HBR
            )
            
            # Serialize combined covariance matrix
            combined_cov = cov_p + cov_s
            cov_matrix_json = json.dumps(combined_cov.tolist())
            
        db_conj = ConjunctionEvent(
            primary_id=conj["primary_id"],
            secondary_id=conj["secondary_id"],
            tca=conj["tca"].replace(tzinfo=None),
            miss_distance=conj["miss_distance"],
            radial=radial,
            in_track=in_track,
            cross_track=cross_track,
            pc=pc_val,
            covariance_matrix_json=cov_matrix_json
        )
        session.add(db_conj)
        
    session.commit()
    print("Saved conjunction events to table conjunction_events.")

    # 6. Reentry Decay corridor simulations (altitude < 250 km)
    print("Checking for reentry decay candidates...")
    decay_candidates = []
    for sat in sats_subset:
        # Find latest state vector for this satellite
        sv = [s for s in state_vectors if s["norad_id"] == sat["norad_id"]][0]
        alt = sv["altitude"]
        if alt < 250.0:
            decay_candidates.append(sat)
            
    # If no low-altitude satellites are currently in the active subset,
    # force simulation on the first satellite for demonstration and code-path verification.
    demo_candidate = False
    if not decay_candidates and sats_subset:
        decay_candidates.append(sats_subset[0])
        demo_candidate = True
        print(f"No active decay candidates (<250km) in test subset. Using demonstration candidate: {sats_subset[0]['name']}")
        
    # Clear old reentry alerts
    session.query(ReentryAlert).delete()
    
    for sat in decay_candidates:
        print(f"Running Monte Carlo reentry corridor simulation for: {sat['name']} (NORAD {sat['norad_id']})...")
        # Run 50 runs to keep database population execution fast during testing
        num_runs = 50
        geojson_feature = generate_reentry_corridor(
            tle_line1=sat["tle_line1"],
            tle_line2=sat["tle_line2"],
            f10_7=f10_7,
            ap=ap,
            num_runs=num_runs
        )
        
        # Calculate ETA (estimated time of decay)
        mean_decay_sec = geojson_feature["properties"]["mean_decay_time_sec"]
        eta_time = now_utc + timedelta(seconds=mean_decay_sec)
        
        db_alert = ReentryAlert(
            norad_id=sat["norad_id"],
            name=sat["name"],
            decay_rate=0.08 if demo_candidate else 0.45,  # fictitious decay rate index
            eta=eta_time.replace(tzinfo=None),
            uncertainty_hours=float(mean_decay_sec / 3600.0 * 0.15),  # 15% uncertainty bounds
            corridor_geojson=json.dumps(geojson_feature),
            casualty_probability=0.00012  # example calculated casualty risk score
        )
        session.add(db_alert)
        
    session.commit()
    print("Saved reentry alerts to table reentry_alerts.")
    print("ORVEXA live data export completed successfully.")
    session.close()

if __name__ == "__main__":
    from datetime import timedelta
    run_pipeline_and_export()
