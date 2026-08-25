import os
import time
from datetime import datetime, timedelta, timezone
import requests
from skyfield.api import load, wgs84, EarthSatellite

def fetch_active_catalog(cache_path: str = "active_tle_cache.txt", force_refresh: bool = False) -> list[dict]:
    """
    Downloads the active satellite TLE file directly from CelesTrak.
    Parses the 3-line format to extract name, NORAD ID, TLE line 1, and TLE line 2.
    Implements local file caching to prevent rate-limiting during test runs.
    """
    content = None
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"Loaded active catalog from local cache: {cache_path}")
        except Exception as e:
            print(f"Error reading cache: {e}. Downloading instead.")

    if not content:
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        print(f"Fetching active catalog from CelesTrak: {url}")
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            content = response.text
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Saved active catalog to cache: {cache_path}")
            except Exception as e:
                print(f"Error writing cache: {e}")
        except Exception as e:
            print(f"Warning: Failed to fetch active catalog from CelesTrak ({e}). Using offline dummy fallback catalog.")
            # Dummy fallback TLE data (contains payloads, debris, and rocket bodies)
            content = """ISS (ZARYA)
1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998
2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408
CALSPHERE 1
1 00900U 64063C   20351.52044444  .00001000  00000-0  26000-4 0  9998
2 00900  90.0000 120.0000 0001000  45.0000 270.0000 14.50000000000000
TIANHE-1
1 48274U 21035A   21120.52044444  .00001200  00000-0  30000-4 0  9998
2 48274  41.5000 160.0000 0008000  50.0000 310.0000 15.62000000000000
FENGYUN 1C DEBRIS
1 90001U 07002A   20351.52044444  .00001000  00000-0  26000-4 0  9998
2 90001  98.6467  44.5727 0002164  73.9623  34.8726 14.19280000260408
COSMOS 2251 DEBRIS
1 90002U 93036A   20351.52044444  .00002000  00000-0  51000-4 0  9998
2 90002  74.0467  65.5727 0012164  80.9623  25.8726 14.59280000260408
SL-16 ROCKET BODY
1 90003U 92055B   20351.52044444  .00001500  00000-0  32000-4 0  9998
2 90003  71.0123  88.5727 0005164  60.9623  40.8726 15.02100000260408
CZ-4C ROCKET BODY
1 90004U 15003B   20351.52044444  .00001200  00000-0  28000-4 0  9998
2 90004  98.2104 110.5727 0001164  50.9623  55.8726 14.85100000260408
"""

    lines = content.strip().split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    satellites = []
    # Parse 3-line format
    for i in range(0, len(lines) - 2, 3):
        name_line = lines[i]
        line1 = lines[i+1]
        line2 = lines[i+2]

        if name_line.startswith("0 "):
            name = name_line[2:].strip()
        else:
            name = name_line.strip()

        # NORAD catalog ID is columns 3-7 in TLE line 1 (inclusive)
        # e.g., "1 25544U..." -> "25544"
        try:
            norad_id = int(line1[2:7].strip())
        except ValueError:
            continue

        satellites.append({
            "norad_id": norad_id,
            "name": name,
            "tle_line1": line1,
            "tle_line2": line2
        })

    print(f"Parsed {len(satellites)} satellites from the catalog.")
    return satellites

def propagate_catalog_batch(tle_list: list, time_window_hours: int = 48, step_minutes: int = 10) -> list:
    """
    Iterates through all active satellites in the list.
    Uses SGP4 propagation to calculate TEME position [x, y, z] (km) and velocity [vx, vy, vz] (km/s) vectors.
    Converts to ECEF/WGS84 geodetic coordinates (latitude, longitude, altitude) for visualization.
    Returns a structured list of state vectors over the time window.
    """
    # Load timescale offline using built-in data to prevent downloading files during runs
    ts = load.timescale(builtin=True)

    start_time = datetime.now(timezone.utc)
    time_steps = [
        start_time + timedelta(minutes=m)
        for m in range(0, time_window_hours * 60 + 1, step_minutes)
    ]
    t_array = ts.from_datetimes(time_steps)

    state_vectors = []

    for sat_dict in tle_list:
        try:
            sat = EarthSatellite(
                sat_dict["tle_line1"],
                sat_dict["tle_line2"],
                sat_dict["name"],
                ts
            )
            # Propagate vectorized over the times
            geocentric = sat.at(t_array)
            
            positions = geocentric.position.km  # Shape (3, N)
            velocities = geocentric.velocity.km_per_s  # Shape (3, N)
            
            subpoints = wgs84.subpoint(geocentric)
            lats = subpoints.latitude.degrees
            lons = subpoints.longitude.degrees
            alts = subpoints.elevation.km

            for idx, dt in enumerate(time_steps):
                state_vectors.append({
                    "norad_id": sat_dict["norad_id"],
                    "name": sat_dict["name"],
                    "epoch": dt,
                    "position_x": float(positions[0, idx]),
                    "position_y": float(positions[1, idx]),
                    "position_z": float(positions[2, idx]),
                    "velocity_x": float(velocities[0, idx]),
                    "velocity_y": float(velocities[1, idx]),
                    "velocity_z": float(velocities[2, idx]),
                    "latitude": float(lats[idx]),
                    "longitude": float(lons[idx]),
                    "altitude": float(alts[idx])
                })
        except Exception as e:
            # Handle potential propagation errors gracefully (e.g. decayed satellites or numerical issues)
            print(f"Error propagating satellite {sat_dict.get('norad_id', 'unknown')}: {e}")
            continue

    return state_vectors

if __name__ == "__main__":
    print("Running ORVEXA Propagator Standalone Script...")
    start_perf = time.perf_counter()

    # Step 1: Fetch active TLEs
    active_sats = fetch_active_catalog()

    # Step 2: Propagate the first 100 satellites
    test_sats = active_sats[:100]
    print(f"Propagating {len(test_sats)} satellites over 48 hours with 10-minute steps...")
    
    state_vectors = propagate_catalog_batch(test_sats, time_window_hours=48, step_minutes=10)
    
    end_perf = time.perf_counter()
    duration = end_perf - start_perf

    print(f"Successfully generated {len(state_vectors)} state vectors in {duration:.3f} seconds.")
    if state_vectors:
        print("\nSample State Vector:")
        for k, v in state_vectors[0].items():
            print(f"  {k}: {v}")
