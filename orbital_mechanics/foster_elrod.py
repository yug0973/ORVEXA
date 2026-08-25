import numpy as np
from scipy.special import ive

def calculate_foster_elrod(primary_state, secondary_state, primary_cov, secondary_cov, hbr: float = 10.0) -> float:
    """
    Calculate the Probability of Collision (Pc) using Chan's analytical approximation 
    of the 2D B-plane integral.
    
    Parameters:
    - primary_state: tuple/list of (r_p, v_p) where r_p is position (km), v_p is velocity (km/s)
    - secondary_state: tuple/list of (r_s, v_s) where r_s is position (km), v_s is velocity (km/s)
    - primary_cov: 3x3 position covariance matrix of primary object (km^2)
    - secondary_cov: 3x3 position covariance matrix of secondary object (km^2)
    - hbr: Hard Body Radius in meters (default 10.0)
    
    Returns:
    - Pc: float, the numerical probability of collision (0.0 to 1.0)
    """
    from orbital_mechanics.chan_pc import calculate_chan_pc_detailed
    res = calculate_chan_pc_detailed(
        primary_state=primary_state,
        secondary_state=secondary_state,
        primary_cov=primary_cov,
        secondary_cov=secondary_cov,
        hbr=hbr
    )
    return res["pc"]

if __name__ == "__main__":
    print("Running Foster-Elrod / Chan Pc Calculator Standalone Script...")
    
    # Test Scenario: Conjunction case with close approach
    r_p = [4200.0, 3100.0, 5000.0]  # km
    v_p = [5.1, 4.2, 3.8]          # km/s
    
    # Secondary passing close to primary
    r_s = [4200.05, 3100.02, 5000.01]  # km (50m, 20m, 10m offset)
    v_s = [5.1, 4.2, 5.8]             # km/s (relative velocity along Z-axis)
    
    # Positional Covariance Matrices (ECI, in km^2)
    # primary: standard deviation of ~10m in position
    cov_p = np.diag([1e-4, 1e-4, 1e-4]) 
    # secondary: standard deviation of ~20m in position
    cov_s = np.diag([4e-4, 4e-4, 4e-4])
    
    Pc = calculate_foster_elrod(
        primary_state=(r_p, v_p),
        secondary_state=(r_s, v_s),
        primary_cov=cov_p,
        secondary_cov=cov_s,
        hbr=15.0 # 15 meters HBR
    )
    
    print(f"Computed Collision Probability (Pc): {Pc:.8e}")
