import numpy as np
from datetime import datetime, timedelta

import importlib.util

# Optional high-precision NRLMSISE-00 C-extension
NRLMSISE00_AVAILABLE = False
nrlmsise00 = None

try:
    if importlib.util.find_spec("nrlmsise00") is not None:
        import nrlmsise00  # type: ignore
        NRLMSISE00_AVAILABLE = True
except Exception:
    NRLMSISE00_AVAILABLE = False

# Constants
MU = 398600.4418      # km^3/s^2 (Standard gravitational parameter)
R_E = 6378.137        # km (Earth equatorial radius)
J2 = 1.08262668e-3    # J2 gravity perturbation coefficient
OMEGA_E = 7.292115e-5 # rad/s (Earth's angular rotation rate)

def get_density_fallback(alt_km: float, f107: float = 150.0, ap: float = 15.0) -> float:
    """
    High-fidelity numerical fallback density profile (80 km to 1000 km) 
    interpolated from reference MSIS log-densities, scaled dynamically 
    by solar flux (F10.7) and geomagnetic index (Ap).
    
    Returns:
    - density in kg/m^3
    """
    # Reference altitude grid and log10 density values at F10.7 = 150, Ap = 15
    ref_alts = np.array([
        80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 
        180.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0, 800.0, 1000.0
    ])
    ref_log_rhos = np.array([
        -4.74, -5.47, -6.25, -7.02, -7.66, -8.09, -8.42, -8.70, 
        -9.27, -9.57, -10.14, -10.62, -11.43, -12.09, -12.64, -13.52, -14.22
    ])
    
    # Clip alt_km to the boundary limits
    alt_clip = np.clip(alt_km, 80.0, 1000.0)
    log_rho_interp = np.interp(alt_clip, ref_alts, ref_log_rhos)
    rho_base = 10.0 ** log_rho_interp
    
    # Altitude-dependent solar expansion factor (thermosphere expands as solar activity heats it)
    alt_factor = np.clip((alt_clip - 80.0) / 200.0, 0.0, None)
    
    f_effect = 1.0 + 1.5 * ((f107 - 150.0) / 150.0) * (alt_factor ** 1.5)
    ap_effect = 1.0 + 0.1 * ((ap - 15.0) / 150.0) * (alt_factor ** 1.0)
    
    rho = rho_base * np.clip(f_effect, 0.1, 20.0) * np.clip(ap_effect, 0.5, 5.0)
    return float(rho)

def get_atmospheric_density(time_dt: datetime, alt_km: float, lat_deg: float, lon_deg: float, f107a: float, f107: float, ap: float, density_multiplier: float = 1.0) -> float:
    """
    Computes atmospheric density at a given date, altitude, latitude, and longitude.
    Uses NRLMSISE-00 if available, falling back to a high-fidelity numerical approximation.
    
    Returns:
    - density in kg/m^3
    """
    if alt_km < 80.0:
        # Below breakup threshold, return high density
        return 1.8e-5 * density_multiplier
        
    if NRLMSISE00_AVAILABLE:
        try:
            # call msise_model which accepts datetime
            densities, temperatures = nrlmsise00.msise_model(
                time=time_dt,
                alt=alt_km,
                lat=lat_deg,
                lon=lon_deg,
                f107a=f107a,
                f107=f107,
                ap=ap
            )
            # densities[5] is total mass density in g/cm^3.
            # Convert to kg/m^3 by multiplying by 1000.0
            rho = densities[5] * 1000.0
            if not np.isnan(rho) and rho > 0.0:
                return float(rho * density_multiplier)
        except Exception as e:
            # Fallback on error
            pass
            
    return get_density_fallback(alt_km, f107, ap) * density_multiplier

def accel_gravity_j2(r: np.ndarray) -> np.ndarray:
    """
    Computes Earth gravitational acceleration including the J2 oblate perturbation (ECI frame).
    
    Parameters:
    - r: 3-element numpy array representing position in ECI (km)
    
    Returns:
    - gravity acceleration vector in ECI (km/s^2)
    """
    r_mag = np.linalg.norm(r)
    if r_mag < 1e-6:
        return np.zeros(3)
        
    # Standard Newtonian 2-body gravity
    a_g0 = -MU * r / (r_mag ** 3)
    
    # J2 Perturbation
    z = r[2]
    z2_r2 = (z / r_mag) ** 2
    
    factor = (1.5 * J2 * MU * R_E**2) / (r_mag**5)
    ax_j2 = factor * r[0] * (5.0 * z2_r2 - 1.0)
    ay_j2 = factor * r[1] * (5.0 * z2_r2 - 1.0)
    az_j2 = factor * r[2] * (5.0 * z2_r2 - 3.0)
    
    a_j2 = np.array([ax_j2, ay_j2, az_j2])
    return a_g0 + a_j2

def accel_drag(r: np.ndarray, v: np.ndarray, Cd_A_over_m: float, rho: float) -> np.ndarray:
    """
    Computes drag acceleration vector in the ECI frame, accounting for co-rotating atmosphere.
    
    Parameters:
    - r: position vector in ECI (km)
    - v: velocity vector in ECI (km/s)
    - Cd_A_over_m: ballistic parameter (Cd * A / m) in m^2/kg
    - rho: atmospheric density in kg/m^3
    
    Returns:
    - drag acceleration vector in ECI (km/s^2)
    """
    # Co-rotating atmosphere velocity: v_atm = w_e x r
    # v_atm = [-omega_e * y, omega_e * x, 0]
    v_atm = np.array([-OMEGA_E * r[1], OMEGA_E * r[0], 0.0])
    
    v_rel = v - v_atm
    v_rel_norm = np.linalg.norm(v_rel)
    
    # Acceleration in ECI (km/s^2)
    # accel_drag = -0.5 * Cd * (A/m) * rho * V_rel * V_rel_vector
    # Convert density from kg/m^3 to kg/km^3 by multiplying by 10^9
    # Convert Cd * A / m from m^2/kg to km^2/kg by dividing by 10^6
    # Combined conversion factor: 10^9 / 10^6 = 1000.0
    a_d = -0.5 * Cd_A_over_m * rho * 1000.0 * v_rel_norm * v_rel
    return a_d

def decay_derivatives(t_sec: float, y: np.ndarray, Cd_A_over_m: float, f107a: float, f107: float, ap: float, epoch_start: datetime, ts) -> np.ndarray:
    """
    Calculates derivatives of motion for numerical integration.
    y = [x, y, z, vx, vy, vz]
    """
    r = y[0:3]
    v = y[3:6]
    
    r_mag = np.linalg.norm(r)
    alt = r_mag - R_E
    
    # 1. Compute atmospheric density at position
    t_curr = epoch_start + timedelta(seconds=float(t_sec))
    
    # Estimate lat/lon from ECI (approximate for density lookup)
    t_sf = ts.from_datetime(t_curr)
    # Simple estimation or WGS84 mapping
    # To keep it fast, we can convert simple GMST
    gmst = t_sf.gmst * 15.0 # degrees
    lon = np.degrees(np.arctan2(r[1], r[0])) - gmst
    lon = (lon + 180.0) % 360.0 - 180.0
    lat = np.degrees(np.arcsin(r[2] / r_mag)) if r_mag > 0 else 0.0
    
    rho = get_atmospheric_density(t_curr, alt, lat, lon, f107a, f107, ap)
    
    from orbital_mechanics.solar_weather import get_drag_coefficient_scaler
    scaler = get_drag_coefficient_scaler(f107)
    rho = rho * scaler
    
    # 2. Compute accelerations
    a_g = accel_gravity_j2(r)
    a_d = accel_drag(r, v, Cd_A_over_m, rho)
    
    a_total = a_g + a_d
    
    return np.hstack([v, a_total])

if __name__ == "__main__":
    print("Running Decay Engine Verification Script...")
    
    # Check fallback vs real
    print(f"NRLMSISE-00 Available: {NRLMSISE00_AVAILABLE}")
    
    # Test altitude density profile
    print("\nAtmospheric Density Profiles (kg/m^3):")
    dt = datetime(2026, 8, 9, 12, 0, 0)
    for alt in [120, 150, 200, 300, 400]:
        rho_nrl = get_atmospheric_density(dt, alt, 0, 0, 150, 150, 15)
        rho_fb = get_density_fallback(alt, 150, 15)
        print(f"  Alt {alt} km: NRLMSISE00 = {rho_nrl:.6e} | Fallback = {rho_fb:.6e}")
