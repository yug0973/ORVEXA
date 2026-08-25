import os
import time
import json
import requests
from datetime import datetime

def fetch_live_noaa_data(cache_path: str = "solar_weather_cache.json", force_refresh: bool = False) -> dict:
    """
    Queries NOAA's live solar weather JSON feeds for the latest F10.7 and Ap values.
    Caches the results locally to avoid excessive NOAA server requests.
    """
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            # Expiration policy: 24 hours (86400 seconds)
            if time.time() - data.get("timestamp", 0) < 86400:
                print(f"Loaded live NOAA solar indices from local cache: {cache_path}")
                return data
        except Exception as e:
            print(f"Error reading cache: {e}. Refetching from NOAA.")

    print("Fetching live NOAA solar weather indices...")
    
    # 1. Fetch Observed F10.7 solar flux from NOAA SWPC
    f10_7 = 150.0  # Quiet-to-moderate sun default fallback
    try:
        f107_url = "https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json"
        res = requests.get(f107_url, timeout=15)
        res.raise_for_status()
        f107_data = res.json()
        
        # Traverse backwards to find the latest valid monthly observed F10.7
        for entry in reversed(f107_data):
            val = entry.get("f10.7", -1.0)
            if val > 0.0:
                f10_7 = float(val)
                break
    except Exception as e:
        print(f"Warning: Failed to fetch F10.7 from NOAA ({e}). Using default: {f10_7}")

    # 2. Fetch Kp / Ap indices from NOAA SWPC
    ap = 15.0  # Moderate geomagnetic default fallback
    try:
        kp_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        res = requests.get(kp_url, timeout=15)
        res.raise_for_status()
        kp_data = res.json()
        
        # The daily Ap index is the average of the 8 three-hourly running Fredericksburg 'a' values in a 24h window
        a_vals = [entry["a_running"] for entry in kp_data[-8:] if "a_running" in entry]
        if a_vals:
            ap = float(sum(a_vals) / len(a_vals))
    except Exception as e:
        print(f"Warning: Failed to fetch geomagnetic indexes from NOAA ({e}). Using default: {ap}")

    # Cache indices locally
    result = {
        "timestamp": time.time(),
        "f10_7": f10_7,
        "ap": ap
    }
    
    try:
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Cached NOAA indices: F10.7 = {f10_7}, Ap = {ap}")
    except Exception as e:
        print(f"Error writing cache: {e}")
        
    return result

def get_drag_coefficient_scaler(f10_7: float) -> float:
    """
    Computes the drag density scaling factor based on the solar flux.
    Use the ratio of current F10.7 to quiet sun baseline (70 sfu) 
    to scale the atmospheric density lookup.
    """
    return float(f10_7 / 70.0)

def fetch_aditya_l1_data(cache_path: str = "solar_weather_cache.json", trigger_path: str = "aditya_trigger.json") -> dict:
    """
    Generates high-fidelity real-time simulated Aditya-L1 solar observations (SoLEXS & HEL1OS)
    and models CME transit propagation and geomagnetic storm onset.
    """
    import math
    import random
    
    # 1. Base indices from observed cache
    observed = fetch_live_noaa_data(cache_path=cache_path)
    base_f10_7 = observed["f10_7"]
    base_ap = observed["ap"]
    
    now = time.time()
    
    # 2. Setup baseline flux (quiet fluctuations)
    # SoLEXS baseline oscillates around 1.5e-7 W/m^2 (A/B class background)
    solexs_baseline = 1.5e-7 + 0.3e-7 * math.sin(now / 300.0)
    # HEL1OS baseline counts oscillate around 10 counts/sec
    hel1os_baseline = 10.0 + 2.0 * math.cos(now / 200.0) + random.uniform(-0.5, 0.5)
    hel1os_baseline = max(1.0, hel1os_baseline)
    
    current_solexs = solexs_baseline
    current_hel1os = hel1os_baseline
    active_event_dict = None
    
    f10_7_mod = base_f10_7
    ap_mod = base_ap
    
    # 3. Read trigger file if it exists
    event = None
    if os.path.exists(trigger_path):
        try:
            with open(trigger_path, "r") as f:
                event = json.load(f)
        except Exception as e:
            print(f"Error reading trigger file: {e}")
            
    # Auto-fallback: trigger minor C-class flare if no active event
    # First 5 minutes of every hour
    if not event:
        hour_sec = int(now) % 3600
        if hour_sec < 300:
            event = {
                "flare_class": "C",
                "start_time": now - hour_sec,
                "peak_time": now - hour_sec + 60.0,
                "end_time": now - hour_sec + 300.0,
                "cme_speed": 450.0,
                "cme_launched": True,
                "cleared": False,
                "auto": True
            }
            
    if event and not event.get("cleared", False):
        start = event["start_time"]
        peak = event["peak_time"]
        end = event["end_time"]
        fclass = event["flare_class"]
        cme_speed = event["cme_speed"]
        
        # Peak values based on flare class
        if fclass == "X":
            peak_solexs = 1.8e-4
            peak_hel1os = 14500.0
            storm_duration = 180.0  # 3 minutes storm window in simulation
            f10_7_increase = 160.0
            ap_increase = 110.0
            demo_transit_sec = 120.0 # CME hits Earth in 2 minutes for demo
        elif fclass == "M":
            peak_solexs = 4.5e-5
            peak_hel1os = 3200.0
            storm_duration = 120.0  # 2 minutes storm window
            f10_7_increase = 65.0
            ap_increase = 45.0
            demo_transit_sec = 80.0  # CME hits Earth in 80 seconds
        else: # C class
            peak_solexs = 4.8e-6
            peak_hel1os = 380.0
            storm_duration = 60.0   # 1 minute storm window
            f10_7_increase = 15.0
            ap_increase = 10.0
            demo_transit_sec = 45.0  # CME hits Earth in 45 seconds
            
        # Is flare active?
        if start <= now <= end:
            if now < peak:
                # Rising phase
                frac = (now - start) / (peak - start)
                current_solexs = solexs_baseline + (peak_solexs - solexs_baseline) * (frac ** 2)
                current_hel1os = hel1os_baseline + (peak_hel1os - hel1os_baseline) * (frac ** 2)
            else:
                # Decay phase
                frac = (now - peak) / (end - peak)
                decay_factor = math.exp(-frac * 4.0)
                current_solexs = solexs_baseline + (peak_solexs - solexs_baseline) * decay_factor
                current_hel1os = hel1os_baseline + (peak_hel1os - hel1os_baseline) * decay_factor
                
            # Add minor noise
            current_solexs += abs(random.gauss(0, current_solexs * 0.03))
            current_hel1os += abs(random.gauss(0, current_hel1os * 0.03))
            
        # CME tracking:
        AU_km = 149597870.7
        elapsed_sec = now - start
        
        # In simulation mode, we accelerate the progress to demo-transit-sec
        cme_progress = min(1.0, elapsed_sec / demo_transit_sec)
        cme_dist_km = cme_progress * AU_km
        
        # Real-world ETA (not compressed)
        real_total_transit_sec = AU_km / cme_speed
        real_remaining_sec = max(0.0, real_total_transit_sec - (elapsed_sec * (real_total_transit_sec / demo_transit_sec)))
        
        # Demo ETA (compressed for live countdown)
        demo_remaining_sec = max(0.0, demo_transit_sec - elapsed_sec)
        
        impact_active = False
        impact_end = start + demo_transit_sec + storm_duration
        
        if cme_progress >= 1.0 and now < impact_end:
            impact_active = True
            f10_7_mod += f10_7_increase
            ap_mod += ap_increase
            
        active_event_dict = {
            "flare_class": fclass,
            "start_time": start,
            "peak_time": peak,
            "end_time": end,
            "cme_speed": cme_speed,
            "cme_progress_pct": cme_progress,
            "cme_distance_km": cme_dist_km,
            "real_eta_seconds": real_remaining_sec,
            "demo_eta_seconds": demo_remaining_sec,
            "impact_active": impact_active,
            "impact_end_time": impact_end,
            "f10_7_increase": f10_7_increase if impact_active else 0.0,
            "ap_increase": ap_increase if impact_active else 0.0
        }
        
    return {
        "timestamp": now,
        "solexs_flux": current_solexs,
        "hel1os_flux": current_hel1os,
        "f10_7": f10_7_mod,
        "ap": ap_mod,
        "active_event": active_event_dict
    }

def trigger_aditya_flare(flare_class: str, trigger_path: str = "aditya_trigger.json") -> dict:
    """
    Triggers a simulated solar flare event of a specified class ('C', 'M', or 'X').
    Writes the parameters to a local trigger configuration file.
    """
    import time
    
    flare_class = flare_class.upper()
    if flare_class == "X":
        cme_speed = 1800.0  # km/s
        duration = 60.0     # 1 minute flare duration
    elif flare_class == "M":
        cme_speed = 950.0   # km/s
        duration = 45.0     # 45 seconds flare duration
    else:
        flare_class = "C"
        cme_speed = 450.0   # km/s
        duration = 30.0     # 30 seconds flare duration
        
    now = time.time()
    event = {
        "flare_class": flare_class,
        "start_time": now,
        "peak_time": now + 15.0,  # peaks in 15 seconds for interactive speed
        "end_time": now + duration,
        "cme_speed": cme_speed,
        "cme_launched": True,
        "cleared": False
    }
    
    with open(trigger_path, "w") as f:
        json.dump(event, f, indent=2)
        
    return event

def clear_aditya_flare(trigger_path: str = "aditya_trigger.json"):
    """
    Clears any active simulated flare events.
    """
    if os.path.exists(trigger_path):
        try:
            os.remove(trigger_path)
        except Exception as e:
            print(f"Error removing trigger file: {e}")

if __name__ == "__main__":
    print("Running Live NOAA Solar Weather Ingestion...")
    weather = fetch_live_noaa_data(force_refresh=True)
    print("\nParsed Solar Weather Info:")
    for k, v in weather.items():
        if k == "timestamp":
            print(f"  timestamp: {datetime.fromtimestamp(v)}")
        else:
            print(f"  {k}: {v}")
            
    scaler = get_drag_coefficient_scaler(weather["f10_7"])
    print(f"\nComputed Density Scaler: {scaler:.4f}")

