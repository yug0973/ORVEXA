import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from orbital_mechanics.foster_elrod import calculate_foster_elrod
from orbital_mechanics.screening import screen_conjunctions

def test_foster_elrod_centered_isotropic():
    """
    Test Foster-Elrod with a perfectly centered collision (zero miss distance)
    and isotropic covariance.
    Analytical Pc = 1 - exp(-HBR^2 / (2 * sigma^2)).
    With HBR = 10m (0.01 km) and combined sigma = 10m (0.01 km):
    Pc = 1 - exp(-0.5) = 0.39346934028.
    """
    primary_state = ([4200.0, 3100.0, 5000.0], [5.0, 4.0, 3.0])
    secondary_state = ([4200.0, 3100.0, 5000.0], [5.0, 4.0, 5.0]) # zero offset, relative velocity along z
    
    # Combined uncertainty: sigma = 10m (0.01 km) isotropic
    primary_cov = np.diag([0.5e-4, 0.5e-4, 0.5e-4])
    secondary_cov = np.diag([0.5e-4, 0.5e-4, 0.5e-4])
    
    Pc = calculate_foster_elrod(
        primary_state=primary_state,
        secondary_state=secondary_state,
        primary_cov=primary_cov,
        secondary_cov=secondary_cov,
        hbr=10.0
    )
    
    expected_Pc = 1.0 - np.exp(-0.5)
    assert pytest.approx(Pc, abs=1e-7) == expected_Pc

def test_foster_elrod_known_offset():
    """
    Test Foster-Elrod with a known offset scenario.
    Primary state at (0, 0, 0) relative, offsets: 50m, 20m, 10m.
    Combined covariance has std dev of ~22.36m.
    Matches the standalone script result: 1.49596888e-02.
    """
    primary_state = ([4200.0, 3100.0, 5000.0], [5.1, 4.2, 3.8])
    secondary_state = ([4200.05, 3100.02, 5000.01], [5.1, 4.2, 5.8])
    
    cov_p = np.diag([1e-4, 1e-4, 1e-4])
    cov_s = np.diag([4e-4, 4e-4, 4e-4])
    
    Pc = calculate_foster_elrod(
        primary_state=primary_state,
        secondary_state=secondary_state,
        primary_cov=cov_p,
        secondary_cov=cov_s,
        hbr=15.0
    )
    
    assert pytest.approx(Pc, abs=1e-7) == 1.49596888e-02

def test_foster_elrod_zero_probability():
    """
    Test Foster-Elrod when the miss distance is extremely large (e.g. 50 km)
    relative to position covariance (std dev of 20m). Pc should be 0.0.
    """
    primary_state = ([4200.0, 3100.0, 5000.0], [7.0, 0.0, 0.0])
    secondary_state = ([4250.0, 3100.0, 5000.0], [0.0, 7.0, 0.0]) # 50 km miss distance
    
    cov_p = np.diag([1e-4, 1e-4, 1e-4])
    cov_s = np.diag([1e-4, 1e-4, 1e-4])
    
    Pc = calculate_foster_elrod(
        primary_state=primary_state,
        secondary_state=secondary_state,
        primary_cov=cov_p,
        secondary_cov=cov_s,
        hbr=10.0
    )
    
    assert Pc == 0.0

def test_screen_conjunctions_synthetic():
    """
    Test spatial KD-Tree screening and TCA refinement.
    Create two satellites moving along perpendicular trajectories that cross near the origin.
    Sat A: moving from (-15, 0, 0) to (15, 0, 0) at 1 km/s.
    Sat B: moving from (0, -15, 0) to (0, 15, 0) at 1 km/s.
    They should cross closest at t = 15 seconds.
    """
    t_start = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    
    state_vectors = []
    # Build state vectors at 10-second steps
    for step in range(4): # t = 0, 10, 20, 30 seconds
        dt = t_start + timedelta(seconds=step * 10)
        
        # Sat A: x = -15 + step*10, y = 0, z = 0
        pos_A = [-15.0 + step * 10.0, 0.0, 0.0]
        vel_A = [1.0, 0.0, 0.0]
        
        # Sat B: x = 0, y = -15 + step*10, z = 0 (offset by 0.05 km in z for a 50m miss distance)
        pos_B = [0.0, -15.0 + step * 10.0, 0.05]
        vel_B = [0.0, 1.0, 0.0]
        
        state_vectors.append({
            "norad_id": 10001,
            "name": "SAT_A",
            "epoch": dt,
            "position_x": pos_A[0],
            "position_y": pos_A[1],
            "position_z": pos_A[2],
            "velocity_x": vel_A[0],
            "velocity_y": vel_A[1],
            "velocity_z": vel_A[2]
        })
        
        state_vectors.append({
            "norad_id": 10002,
            "name": "SAT_B",
            "epoch": dt,
            "position_x": pos_B[0],
            "position_y": pos_B[1],
            "position_z": pos_B[2],
            "velocity_x": vel_B[0],
            "velocity_y": vel_B[1],
            "velocity_z": vel_B[2]
        })

    # Screen conjunctions with 10 km threshold
    # At t = 10s: pos_A = (-5, 0, 0), pos_B = (0, -5, 0.05). Dist = sqrt(25 + 25) = 7.07 km (within threshold)
    # At t = 20s: pos_A = (5, 0, 0), pos_B = (0, 5, 0.05). Dist = 7.07 km (within threshold)
    # At closest approach (t = 15s): pos_A = (0, 0, 0), pos_B = (0, 0, 0.05). Dist = 50m (0.05 km)
    candidates = screen_conjunctions(state_vectors, threshold_km=10.0)
    
    assert len(candidates) == 1
    cand = candidates[0]
    
    assert cand["primary_id"] == 10001
    assert cand["secondary_id"] == 10002
    
    # Refined TCA should be exactly at 12:00:15
    expected_tca = t_start + timedelta(seconds=15)
    assert cand["tca"] == expected_tca
    
    # Refined miss distance should be 0.05 km (50 meters)
    assert pytest.approx(cand["miss_distance"], abs=1e-5) == 0.05
    assert pytest.approx(cand["miss_vector"][2], abs=1e-5) == -0.05
