import numpy as np
from datetime import datetime, timedelta
import math
from typing import List, Dict, Any, Tuple
from skyfield.api import load
from orbital_mechanics.decay_engine import decay_derivatives

def inverse_transform_sample_Lc(N_total: float, M_total: float, num_samples: int) -> np.ndarray:
    """
    Inverse transform sampling for characteristic length Lc.
    CDF(Lc) = 1 - N(Lc)/N_total
    N(Lc) = 0.1 * (M_total)^0.75 * Lc^-1.71
    => Lc = ( (1 - u) * N_total / (0.1 * M_total^0.75) ) ^ (-1/1.71)
    """
    u = np.random.uniform(0, 1, num_samples)
    coeff = 0.1 * (M_total ** 0.75)
    
    val = (1 - u) * N_total / coeff
    val = np.maximum(val, 1e-10)
    
    Lc = np.power(val, -1.0 / 1.71)
    return np.clip(Lc, 0.10, 5.0)

def simulate_breakup(
    primary_mass_kg: float,
    secondary_mass_kg: float,
    v_rel_km_s: float,
    tca: datetime,
    com_position_km: np.ndarray,
    com_velocity_km_s: np.ndarray,
    max_rendered_fragments: int = 300
) -> Dict[str, Any]:
    
    ke_per_mass_j_g = 0.5 * (v_rel_km_s ** 2) * 1000.0
    catastrophic = ke_per_mass_j_g > 40.0
    
    M_total = primary_mass_kg + secondary_mass_kg if catastrophic else min(primary_mass_kg, secondary_mass_kg)
    
    N_total_estimated = 0.1 * (M_total ** 0.75) * (0.10 ** -1.71)
    total_estimated = int(round(N_total_estimated))
    
    rendered_count = min(total_estimated, max_rendered_fragments)
    
    if rendered_count == 0:
        return {
            "catastrophic": bool(catastrophic),
            "total_estimated_fragments": int(total_estimated),
            "rendered_fragment_count": int(rendered_count),
            "kinetic_energy_per_mass_j_g": float(ke_per_mass_j_g),
            "fragments": []
        }
        
    Lc_samples = inverse_transform_sample_Lc(N_total_estimated, M_total, rendered_count)
    fragments = []
    
    log10_Lc = np.log10(Lc_samples)
    A_over_m = np.power(10.0, -0.9906 + 0.7089 * log10_Lc)
    A = np.pi * (Lc_samples / 2.0) ** 2
    masses = A / A_over_m
    
    chi = np.log10(A_over_m)
    mu_v = 0.9 * chi + 2.9
    sigma_v = 0.4
    
    delta_v_mag_m_s = np.exp(np.random.normal(mu_v, sigma_v, rendered_count))
    delta_v_mag_km_s = delta_v_mag_m_s / 1000.0
    
    phi = np.random.uniform(0, np.pi * 2, rendered_count)
    costheta = np.random.uniform(-1, 1, rendered_count)
    sintheta = np.sqrt(1 - costheta**2)
    
    dx = sintheta * np.cos(phi)
    dy = sintheta * np.sin(phi)
    dz = costheta
    
    dir_vectors = np.column_stack((dx, dy, dz))
    dv_vectors = dir_vectors * delta_v_mag_km_s[:, np.newaxis]
    
    momentum_vectors = dv_vectors * masses[:, np.newaxis]
    total_momentum = np.sum(momentum_vectors, axis=0)
    total_mass = np.sum(masses)
    
    abs_momentum = np.sum(np.linalg.norm(momentum_vectors, axis=1))
    residual_ratio = np.linalg.norm(total_momentum) / abs_momentum if abs_momentum > 0 else 0
    
    if residual_ratio > 0.05:
        print(f"Warning: Momentum residual exceeds 5% ({residual_ratio:.2%}). Balancing...")
        dv_correction = total_momentum / total_mass
        dv_vectors -= dv_correction
        
    for i in range(rendered_count):
        vel = com_velocity_km_s + dv_vectors[i]
        
        frag = {
            "id": f"frag_{i:04d}",
            "mass_kg": float(masses[i]),
            "characteristic_length_m": float(Lc_samples[i]),
            "A_over_m": float(A_over_m[i]),
            "initial_position": com_position_km.tolist(),
            "initial_velocity": vel.tolist(),
            "trajectory": [],
            "reentered_at": None
        }
        fragments.append(frag)
        
    return {
        "catastrophic": bool(catastrophic),
        "total_estimated_fragments": int(total_estimated),
        "rendered_fragment_count": int(rendered_count),
        "kinetic_energy_per_mass_j_g": float(ke_per_mass_j_g),
        "fragments": fragments
    }

def propagate_fragments(fragments: List[Dict[str, Any]], start_time: datetime, duration_hrs: float = 6.0, step_s: float = 30.0):
    from datetime import timezone
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
        
    ts = load.timescale(builtin=True)
    steps = int((duration_hrs * 3600) / step_s)
    
    f107a, f107, ap = 150.0, 150.0, 15.0
    
    num_frags = len(fragments)
    states = np.zeros((num_frags, 6))
    
    for i, frag in enumerate(fragments):
        states[i, 0:3] = frag["initial_position"]
        states[i, 3:6] = frag["initial_velocity"]
        
        frag["trajectory"].append({
            "t": 0,
            "eci": [round(float(states[i, 0]), 3), round(float(states[i, 1]), 3), round(float(states[i, 2]), 3)]
        })
        
    active_mask = np.ones(num_frags, dtype=bool)
    
    for step in range(1, steps + 1):
        t_sec = step * step_s
        active_indices = np.where(active_mask)[0]
        if len(active_indices) == 0:
            break
            
        for i in active_indices:
            y = states[i]
            cd_A_m = 2.2 * fragments[i]["A_over_m"] 
            
            k1 = decay_derivatives(t_sec, y, cd_A_m, f107a, f107, ap, start_time, ts)
            k2 = decay_derivatives(t_sec + step_s/2, y + step_s/2 * k1, cd_A_m, f107a, f107, ap, start_time, ts)
            k3 = decay_derivatives(t_sec + step_s/2, y + step_s/2 * k2, cd_A_m, f107a, f107, ap, start_time, ts)
            k4 = decay_derivatives(t_sec + step_s, y + step_s * k3, cd_A_m, f107a, f107, ap, start_time, ts)
            
            states[i] = y + (step_s / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            
            r_mag = np.linalg.norm(states[i, 0:3])
            alt_km = r_mag - 6378.137
            
            if alt_km < 80.0:
                active_mask[i] = False
                reentry_dt = start_time + timedelta(seconds=t_sec)
                fragments[i]["reentered_at"] = reentry_dt.isoformat()
            
            fragments[i]["trajectory"].append({
                "t": int(t_sec),
                "eci": [round(float(states[i, 0]), 3), round(float(states[i, 1]), 3), round(float(states[i, 2]), 3)]
            })
            
    for frag in fragments:
        del frag["initial_position"]
        del frag["initial_velocity"]
        del frag["A_over_m"]
