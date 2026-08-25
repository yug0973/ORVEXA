import numpy as np
from scipy.special import ive

def calculate_chan_pc_detailed(
    primary_state, 
    secondary_state, 
    primary_cov, 
    secondary_cov, 
    hbr: float = 10.0
) -> dict:
    """
    Calculate the Probability of Collision (Pc) using Chan's analytical approximation 
    and return detailed intermediate physical and mathematical parameters.
    
    Parameters:
    - primary_state: tuple/list of (r_p, v_p) where r_p is position (km), v_p is velocity (km/s)
    - secondary_state: tuple/list of (r_s, v_s) where r_s is position (km), v_s is velocity (km/s)
    - primary_cov: 3x3 position covariance matrix of primary object (km^2)
    - secondary_cov: 3x3 position covariance matrix of secondary object (km^2)
    - hbr: Hard Body Radius in meters (default 10.0)
    
    Returns:
    - dict containing:
        - pc: the final collision probability (float)
        - miss_distance_km: norm of the relative position vector in the B-plane
        - sigma_major: semi-major axis of the combined uncertainty ellipse in B-plane (km)
        - sigma_minor: semi-minor axis of the combined uncertainty ellipse in B-plane (km)
        - u: Mahalanobis-style distance term used in the Rician series
        - alpha: normalized miss distance component
        - beta: normalized HBR component
    """
    r_p, v_p = np.array(primary_state[0]), np.array(primary_state[1])
    r_s, v_s = np.array(secondary_state[0]), np.array(secondary_state[1])
    
    r = r_p - r_s  # Relative position vector (km)
    v = v_p - v_s  # Relative velocity vector (km/s)
    
    v_norm = np.linalg.norm(v)
    if v_norm < 1e-6:
        return {
            "pc": 0.0,
            "miss_distance_km": float(np.linalg.norm(r)),
            "sigma_major": 0.0,
            "sigma_minor": 0.0,
            "u": 0.0,
            "alpha": 0.0,
            "beta": 0.0
        }
        
    # 2. Define the B-plane (encounter plane) coordinate system
    e_z = v / v_norm  # Unit vector along relative velocity
    
    if abs(e_z[0]) < 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    else:
        ref = np.array([0.0, 1.0, 0.0])
        
    e_x = np.cross(ref, e_z)
    e_x /= np.linalg.norm(e_x)
    e_y = np.cross(e_z, e_x)
    
    # Projection matrix P (2x3)
    P = np.vstack([e_x, e_y])
    
    # 3. Project relative position and combined covariance onto B-plane
    r_B = P.dot(r)  # 2D relative position in B-plane (km)
    miss_dist = np.linalg.norm(r_B)
    
    C_p = np.array(primary_cov)
    C_s = np.array(secondary_cov)
    C = C_p + C_s   # Combined covariance matrix (km^2)
    
    Sigma_B = P.dot(C).dot(P.T)  # 2D B-plane covariance matrix
    
    # 4. Diagonalize Sigma_B (find principal axes of uncertainty ellipse)
    eigenvalues, eigenvectors = np.linalg.eigh(Sigma_B)
    
    # Sort descending to get major/minor axes
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    sigma_x2 = eigenvalues[0]
    sigma_y2 = eigenvalues[1]
    
    sigma_major = np.sqrt(max(sigma_x2, 1e-30))
    sigma_minor = np.sqrt(max(sigma_y2, 1e-30))
    
    # Rotate the B-plane relative position vector into diagonal frame
    r_B_prime = eigenvectors.T.dot(r_B)
    x_m = r_B_prime[0]
    y_m = r_B_prime[1]
    
    # Convert HBR from meters to kilometers
    R_km = hbr / 1000.0
    
    sigma = np.sqrt(sigma_major * sigma_minor)
    
    if sigma < 1e-9:
        Pc = 1.0 if miss_dist <= R_km else 0.0
        u = 0.0
        alpha = 0.0
        beta = 0.0
    else:
        u = (x_m / sigma_major) ** 2 + (y_m / sigma_minor) ** 2  # Mahalanobis distance squared
        v_dist = np.sqrt(u) * sigma
        
        alpha = v_dist / sigma
        beta = R_km / sigma
        
        if alpha == 0.0 and beta == 0.0:
            Pc = 0.0
        else:
            x = alpha * beta
            factor = np.exp(-0.5 * (alpha - beta) ** 2)
            tol = 1e-16
            max_terms = 500
            
            if beta >= alpha:
                ratio = alpha / beta if beta > 0.0 else 0.0
                term_sum = 0.0
                for k in range(max_terms):
                    term = (ratio ** k) * ive(k, x)
                    term_sum += term
                    if term < tol * term_sum and k > 5:
                        break
                Pc = 1.0 - factor * term_sum
            else:
                ratio = beta / alpha
                term_sum = 0.0
                for k in range(1, max_terms):
                    term = (ratio ** k) * ive(k, x)
                    term_sum += term
                    if term < tol * term_sum and k > 5:
                        break
                Pc = factor * term_sum
                
    Pc = float(max(0.0, min(1.0, Pc)))
    
    return {
        "pc": Pc,
        "miss_distance_km": float(miss_dist),
        "sigma_major": float(sigma_major),
        "sigma_minor": float(sigma_minor),
        "u": float(u),
        "alpha": float(alpha),
        "beta": float(beta)
    }
