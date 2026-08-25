import numpy as np
import json
from datetime import datetime, timedelta, timezone
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, MultiPolygon, mapping
from skyfield.api import load, EarthSatellite, Distance, wgs84
from skyfield.positionlib import Geocentric

from orbital_mechanics.decay_engine import get_atmospheric_density, decay_derivatives

def generate_reentry_corridor(tle_line1: str, tle_line2: str, f10_7: float = 150.0, ap: float = 15.0, num_runs: int = 1000, density_multiplier: float = 1.0) -> dict:
    """
    Propagates a satellite downward from its initial state to the 80 km breakup threshold
    running parallel (vectorized) Monte Carlo simulations with perturbed ballistic coefficients 
    (+/- 20%) and density factors (+/- 15%). Computes the convex hull and returns a GeoJSON 
    MultiPolygon corridor.
    """
    ts = load.timescale(builtin=True)
    
    # 1. Parse TLE and extract initial state at epoch
    sat = EarthSatellite(tle_line1, tle_line2, "SATELLITE", ts)
    t_sf = sat.epoch
    epoch = t_sf.utc_datetime()
    geocentric = sat.at(t_sf)
    
    r_eci = geocentric.position.km
    v_eci = geocentric.velocity.km_per_s
    
    # Extract B* drag term from SGP4 model
    bstar = getattr(sat.model, 'bstar', 0.0)
    
    # Convert B* to Cd * A / m. Nominal factor in SGP4: Cd * A / m = B* / (rho_0_scaled)
    # We use a standard conversion of Cd*A/m = B* * 40633.0
    if bstar > 0.0:
        Cd_A_over_m = bstar * 40633.0
    else:
        Cd_A_over_m = 0.01  # nominal fallback of 0.01 m^2/kg
        
    Cd_A_over_m = max(Cd_A_over_m, 0.01)  # clamp to ensure decay happens rapidly

    # 2. Check initial altitude and scale down to 120 km if orbit is stable
    r_mag = np.linalg.norm(r_eci)
    alt = r_mag - 6378.137
    
    if alt > 120.0:
        # Scale position to 120 km reentry interface altitude
        r_scale = (6378.137 + 120.0) / r_mag
        r_eci = r_eci * r_scale
        
        # Scale velocity to circular speed at 120 km altitude
        v_mag = np.linalg.norm(v_eci)
        v_circ = np.sqrt(398600.4418 / (6378.137 + 120.0))
        v_eci = v_eci * (v_circ / v_mag)

    # 3. Pre-sample perturbations for Monte Carlo runs
    # Ballistic coefficient Cd*A/m perturbed by +/- 20% (uniform)
    delta_B = np.random.uniform(-0.20, 0.20, num_runs)
    Cd_A_vals = Cd_A_over_m * (1.0 + delta_B)
    
    # Local density factor perturbed by +/- 15% (uniform)
    delta_rho = np.random.uniform(-0.15, 0.15, num_runs)
    rho_factors = 1.0 + delta_rho
    
    # Combined parameter for drag calculation (B * rho_factor)
    B_vals = Cd_A_vals * rho_factors

    # 4. Vectorized integration loop down to 80 km
    init_state = np.hstack([r_eci, v_eci])
    states = np.tile(init_state, (num_runs, 1))  # shape (num_runs, 6)
    
    decayed = np.zeros(num_runs, dtype=bool)
    decay_points = np.zeros((num_runs, 3))
    decay_times = np.zeros(num_runs)
    
    dt = 1.0  # 1-second integration step
    t = 0.0
    max_duration = 3600.0 * 2  # 2 hours maximum
    steps = int(max_duration / dt)
    
    # Gravity/atmosphere parameters
    MU = 398600.4418
    R_E = 6378.137
    J2 = 1.08262668e-3
    OMEGA_E = 7.292115e-5

    def derivs_vectorized(y_states, B_val_array, rho_val_nom, alt_val_nom):
        r_arr = y_states[:, 0:3]
        v_arr = y_states[:, 3:6]
        r_mag_arr = np.linalg.norm(r_arr, axis=1, keepdims=True)
        alts_arr = r_mag_arr - R_E
        
        # J2 oblate gravity acceleration
        z_arr = r_arr[:, 2:3]
        z2_r2_arr = (z_arr / r_mag_arr) ** 2
        factor_arr = (1.5 * J2 * MU * R_E**2) / (r_mag_arr**5)
        
        ax_j2 = factor_arr * r_arr[:, 0:1] * (5.0 * z2_r2_arr - 1.0)
        ay_j2 = factor_arr * r_arr[:, 1:2] * (5.0 * z2_r2_arr - 1.0)
        az_j2 = factor_arr * r_arr[:, 2:3] * (5.0 * z2_r2_arr - 3.0)
        a_j2 = np.hstack([ax_j2, ay_j2, az_j2])
        
        a_grav = -MU * r_arr / (r_mag_arr ** 3) + a_j2
        
        # Co-rotating drag acceleration
        v_atm = np.hstack([-OMEGA_E * r_arr[:, 1:2], OMEGA_E * r_arr[:, 0:1], np.zeros_like(r_arr[:, 2:3])])
        v_rel = v_arr - v_atm
        v_rel_mag = np.linalg.norm(v_rel, axis=1, keepdims=True)
        
        # Scale density by altitude relative to nominal altitude (scale height ~ 6.0 km)
        rho_arr = rho_val_nom * np.exp(-(alts_arr - alt_val_nom) / 6.0)
        
        # a_drag = -0.5 * (Cd*A/m * rho_factor) * rho_scaled * 1000 * v_rel_mag * v_rel
        a_drag = -0.5 * B_val_array[:, np.newaxis] * rho_arr * 1000.0 * v_rel_mag * v_rel
        
        a_total = a_grav + a_drag
        return np.hstack([v_arr, a_total])

    print("Running vectorized Monte Carlo decay integration...")
    for step in range(steps):
        active = ~decayed
        if not np.any(active):
            break
            
        y_active = states[active]
        B_active = B_vals[active]
        
        # Compute nominal active position & altitude
        r_nom = np.mean(y_active[:, 0:3], axis=0)
        alt_nom = np.linalg.norm(r_nom) - R_E
        
        # Query nominal atmospheric density once per step
        t_curr = epoch + timedelta(seconds=float(t))
        t_sf = ts.from_datetime(t_curr)
        gmst = t_sf.gmst * 15.0  # degrees
        lon_nom = np.degrees(np.arctan2(r_nom[1], r_nom[0])) - gmst
        lon_nom = (lon_nom + 180.0) % 360.0 - 180.0
        lat_nom = np.degrees(np.arcsin(r_nom[2] / np.linalg.norm(r_nom)))
        
        rho_nom = get_atmospheric_density(t_curr, alt_nom, lat_nom, lon_nom, f10_7, f10_7, ap, density_multiplier)
        
        from orbital_mechanics.solar_weather import get_drag_coefficient_scaler
        scaler = get_drag_coefficient_scaler(f10_7)
        rho_nom = rho_nom * scaler
        
        # RK4 step
        k1 = derivs_vectorized(y_active, B_active, rho_nom, alt_nom)
        k2 = derivs_vectorized(y_active + 0.5 * dt * k1, B_active, rho_nom, alt_nom)
        k3 = derivs_vectorized(y_active + 0.5 * dt * k2, B_active, rho_nom, alt_nom)
        k4 = derivs_vectorized(y_active + dt * k3, B_active, rho_nom, alt_nom)
        y_new = y_active + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        
        # Check active states that have crossed 80 km threshold
        alts_active = np.linalg.norm(y_new[:, 0:3], axis=1) - R_E
        just_dec = (alts_active <= 80.0)
        
        if np.any(just_dec):
            active_indices = np.where(active)[0]
            dec_indices = active_indices[just_dec]
            
            decay_points[dec_indices] = y_new[just_dec, 0:3]
            decay_times[dec_indices] = t
            decayed[dec_indices] = True
            
        states[active] = y_new
        t += dt

    # Force any remaining active states to register at their current position
    remaining = ~decayed
    if np.any(remaining):
        decay_points[remaining] = states[remaining, 0:3]
        decay_times[remaining] = t
        decayed[remaining] = True

    # 5. Convert ECI positions at 80 km to Geodetic Latitude and Longitude
    print("Converting decay ECI endpoints to geodetic coordinates...")
    lats = []
    lons = []
    
    for i in range(num_runs):
        t_sf = ts.from_datetime(epoch + timedelta(seconds=decay_times[i]))
        pos_eci = decay_points[i]
        
        pos_au = Distance(km=pos_eci).au
        p = Geocentric(pos_au, t=t_sf)
        
        sub = wgs84.subpoint(p)
        lats.append(sub.latitude.degrees)
        lons.append(sub.longitude.degrees)
        
    lats = np.array(lats)
    lons = np.array(lons)

    # 6. Calculate bounding convex hull
    pts = np.column_stack([lons, lats])
    try:
        hull = ConvexHull(pts)
        hull_vertices = pts[hull.vertices]
        # Close the polygon loop
        hull_vertices = np.vstack([hull_vertices, hull_vertices[0]])
        poly = Polygon(hull_vertices)
    except Exception as e:
        print(f"Warning: ConvexHull calculation failed ({e}), using bounding box fallback.")
        min_lon, max_lon = np.min(lons), np.max(lons)
        min_lat, max_lat = np.min(lats), np.max(lats)
        poly = Polygon([
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            (min_lon, min_lat)
        ])
        
    multipoly = MultiPolygon([poly])
    geojson_geom = mapping(multipoly)
    
    geojson_feature = {
        "type": "Feature",
        "geometry": geojson_geom,
        "properties": {
            "satellite_name": getattr(sat, 'name', 'SATELLITE'),
            "norad_id": getattr(sat.model, 'satnum', 0),
            "f10_7": f10_7,
            "ap": ap,
            "simulated_points": num_runs,
            "mean_decay_time_sec": float(np.mean(decay_times))
        }
    }
    
    return geojson_feature

if __name__ == "__main__":
    print("Running Monte Carlo Reentry Corridor Generator Standalone...")
    
    # Test TLE (ISS Zarya)
    line1 = "1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998"
    line2 = "2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408"
    
    corridor = generate_reentry_corridor(line1, line2, f10_7=150.0, ap=15.0, num_runs=100)
    
    print("\nGenerated Corridor GeoJSON Feature:")
    print(json.dumps(corridor, indent=2)[:800] + "\n... [TRUNCATED] ...")
