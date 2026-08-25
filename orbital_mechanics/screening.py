import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import KDTree
from scipy.optimize import minimize_scalar
from skyfield.api import load, EarthSatellite

def screen_conjunctions(state_vectors: list, threshold_km: float = 10.0) -> list[dict]:
    """
    Groups state vectors by epoch slices and screens close approaches using a spatial KD-Tree.
    Refines candidate close-approaches to find the exact Time of Closest Approach (TCA) 
    using numerical optimization of relative position distance over the SGP4 propagation.
    
    Parameters:
    - state_vectors: list of dicts containing norad_id, epoch (datetime), position_x/y/z, velocity_x/y/z
    - threshold_km: screening distance threshold in km (default 10.0)
    
    Returns:
    - list of refined candidate dicts containing primary_id, secondary_id, tca, miss_distance, 
      miss_vector, primary_state, secondary_state.
    """
    if not state_vectors:
        return []

    # 1. Group state vectors by epoch
    epochs = {}
    for sv in state_vectors:
        epoch = sv["epoch"]
        if epoch not in epochs:
            epochs[epoch] = []
        epochs[epoch].append(sv)
        
    # 2. Load TLE map for SGP4 propagation during refinement
    from orbital_mechanics.propagator import fetch_active_catalog
    try:
        tle_list = fetch_active_catalog(cache_path="active_tle_cache.txt")
        tle_map = {sat["norad_id"]: sat for sat in tle_list}
    except Exception as e:
        print(f"Warning: Could not load TLE cache for refinement: {e}")
        tle_map = {}
        
    ts = load.timescale(builtin=True)
    raw_candidates = []
    
    # 3. KD-Tree query for each epoch slice
    for epoch, sv_list in epochs.items():
        if len(sv_list) < 2:
            continue
            
        # Coordinates in km
        coords = np.array([[sv["position_x"], sv["position_y"], sv["position_z"]] for sv in sv_list])
        tree = KDTree(coords)
        pairs = tree.query_pairs(threshold_km)
        
        for i, j in pairs:
            sv_i = sv_list[i]
            sv_j = sv_list[j]
            
            p_id = min(sv_i["norad_id"], sv_j["norad_id"])
            s_id = max(sv_i["norad_id"], sv_j["norad_id"])
            
            # Align primary and secondary state vectors
            sv_prim = sv_i if sv_i["norad_id"] == p_id else sv_j
            sv_sec = sv_j if sv_j["norad_id"] == s_id else sv_i
            
            raw_candidates.append({
                "primary_id": p_id,
                "secondary_id": s_id,
                "epoch_detected": epoch,
                "sv_prim": sv_prim,
                "sv_sec": sv_sec
            })
            
    # 4. Refine close approaches
    refined_candidates = []
    
    # Objective function for distance minimization
    def distance_fn(dt_sec, sat_p, sat_s, epoch_base, ts_obj):
        t_target = epoch_base + timedelta(seconds=float(dt_sec))
        t_sf = ts_obj.from_datetime(t_target)
        pos_p = sat_p.at(t_sf).position.km
        pos_s = sat_s.at(t_sf).position.km
        return np.linalg.norm(pos_p - pos_s)

    for cand in raw_candidates:
        p_id = cand["primary_id"]
        s_id = cand["secondary_id"]
        
        # Fallback to linear relative motion approximation if TLEs are missing
        if p_id not in tle_map or s_id not in tle_map:
            r_p = np.array([cand["sv_prim"]["position_x"], cand["sv_prim"]["position_y"], cand["sv_prim"]["position_z"]])
            v_p = np.array([cand["sv_prim"]["velocity_x"], cand["sv_prim"]["velocity_y"], cand["sv_prim"]["velocity_z"]])
            r_s = np.array([cand["sv_sec"]["position_x"], cand["sv_sec"]["position_y"], cand["sv_sec"]["position_z"]])
            v_s = np.array([cand["sv_sec"]["velocity_x"], cand["sv_sec"]["velocity_y"], cand["sv_sec"]["velocity_z"]])
            
            r_rel = r_p - r_s
            v_rel = v_p - v_s
            v_rel_norm2 = np.dot(v_rel, v_rel)
            
            t_offset_sec = -np.dot(r_rel, v_rel) / v_rel_norm2 if v_rel_norm2 > 1e-9 else 0.0
            t_offset_sec = max(-300.0, min(300.0, t_offset_sec))
            
            refined_tca = cand["epoch_detected"] + timedelta(seconds=t_offset_sec)
            
            # Position offset
            r_p_tca = r_p + v_p * t_offset_sec
            r_s_tca = r_s + v_s * t_offset_sec
            
            miss_vector = r_p_tca - r_s_tca
            miss_dist = np.linalg.norm(miss_vector)
            
            refined_candidates.append({
                "primary_id": p_id,
                "secondary_id": s_id,
                "tca": refined_tca,
                "miss_distance": float(miss_dist),
                "miss_vector": miss_vector.tolist(),
                "primary_state": (r_p_tca.tolist(), v_p.tolist()),
                "secondary_state": (r_s_tca.tolist(), v_s.tolist())
            })
            continue

        # Full numerical optimization refinement via SGP4 propagation
        try:
            tle_p = tle_map[p_id]
            tle_s = tle_map[s_id]
            sat_p = EarthSatellite(tle_p["tle_line1"], tle_p["tle_line2"], tle_p["name"], ts)
            sat_s = EarthSatellite(tle_s["tle_line1"], tle_s["tle_line2"], tle_s["name"], ts)
            
            opt_res = minimize_scalar(
                distance_fn,
                bounds=(-300.0, 300.0),
                method='bounded',
                args=(sat_p, sat_s, cand["epoch_detected"], ts)
            )
            
            best_offset = opt_res.x
            refined_tca = cand["epoch_detected"] + timedelta(seconds=float(best_offset))
            
            t_sf = ts.from_datetime(refined_tca)
            g_p = sat_p.at(t_sf)
            g_s = sat_s.at(t_sf)
            
            pos_p = g_p.position.km
            vel_p = g_p.velocity.km_per_s
            pos_s = g_s.position.km
            vel_s = g_s.velocity.km_per_s
            
            miss_vector = pos_p - pos_s
            miss_dist = np.linalg.norm(miss_vector)
            
            refined_candidates.append({
                "primary_id": p_id,
                "secondary_id": s_id,
                "tca": refined_tca,
                "miss_distance": float(miss_dist),
                "miss_vector": miss_vector.tolist(),
                "primary_state": (pos_p.tolist(), vel_p.tolist()),
                "secondary_state": (pos_s.tolist(), vel_s.tolist())
            })
        except Exception as e:
            print(f"Error refining candidate {p_id} vs {s_id}: {e}")
            continue

    # 5. Deduplicate close-approach candidates detected in adjacent epoch slices
    refined_candidates.sort(key=lambda x: (x["primary_id"], x["secondary_id"], x["tca"]))
    deduped = []
    
    for cand in refined_candidates:
        if not deduped:
            deduped.append(cand)
            continue
        
        last = deduped[-1]
        if last["primary_id"] == cand["primary_id"] and last["secondary_id"] == cand["secondary_id"]:
            # Same pair, verify temporal proximity (within 30 mins)
            t_diff = abs((last["tca"] - cand["tca"]).total_seconds())
            if t_diff < 1800.0:
                # Merge by keeping the closer approach
                if cand["miss_distance"] < last["miss_distance"]:
                    deduped[-1] = cand
                continue
                
        deduped.append(cand)
        
    return deduped
