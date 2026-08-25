import os
import pytest
from orbital_mechanics.propagator import fetch_active_catalog, propagate_catalog_batch

def test_fetch_active_catalog():
    """
    Verify TLE downloader handles files with 1,000+ entries.
    """
    # Use the cached catalog if it exists to be fast and offline-friendly
    cache_file = "active_tle_cache.txt"
    satellites = fetch_active_catalog(cache_path=cache_file)
    
    assert len(satellites) >= 1000
    for sat in satellites[:5]:
        assert "norad_id" in sat
        assert "name" in sat
        assert "tle_line1" in sat
        assert "tle_line2" in sat
        assert len(sat["tle_line1"]) == 69
        assert len(sat["tle_line2"]) == 69

def test_sgp4_propagation_bounds():
    """
    Assert that SGP4 propagation output matches known orbital bounds:
    - LEO altitude (300-2,000 km)
    - GEO altitude (~35,786 km)
    """
    cache_file = "active_tle_cache.txt"
    satellites = fetch_active_catalog(cache_path=cache_file)
    
    leo_sat = None
    geo_sat = None

    # Dynamically find a LEO and GEO satellite in the downloaded catalog
    # using mean motion (revolutions per day) from TLE Line 2 (cols 52-63).
    for sat in satellites:
        line2 = sat["tle_line2"]
        try:
            mean_motion = float(line2[52:63].strip())
        except ValueError:
            continue

        # LEO: mean motion > 11.25 revs/day (period < 128 mins, altitude < 2,000 km)
        if mean_motion > 11.25 and leo_sat is None:
            leo_sat = sat
        
        # GEO: mean motion ~1.0027 revs/day (period ~24 hrs, altitude ~35,786 km)
        if 0.99 <= mean_motion <= 1.01 and geo_sat is None:
            geo_sat = sat

        if leo_sat and geo_sat:
            break

    assert leo_sat is not None, "Could not find a LEO satellite in the active catalog."
    assert geo_sat is not None, "Could not find a GEO satellite in the active catalog."

    print(f"\nTesting propagation bounds for LEO: {leo_sat['name']} (NORAD {leo_sat['norad_id']})")
    print(f"Testing propagation bounds for GEO: {geo_sat['name']} (NORAD {geo_sat['norad_id']})")

    # Propagate both for 48 hours at 1-hour steps
    results = propagate_catalog_batch([leo_sat, geo_sat], time_window_hours=48, step_minutes=60)
    
    # Filter results
    leo_results = [r for r in results if r["norad_id"] == leo_sat["norad_id"]]
    geo_results = [r for r in results if r["norad_id"] == geo_sat["norad_id"]]

    assert len(leo_results) > 0
    assert len(geo_results) > 0

    # Verify LEO altitudes are between 300 and 2,000 km
    for res in leo_results:
        # Give a small buffer of 200-2000 km for eccentric or decaying orbits
        assert 200 <= res["altitude"] <= 2000, f"LEO altitude {res['altitude']} km out of bounds (200-2000 km)"

    # Verify GEO altitudes are around 35,786 km (between 35,000 and 36,500 km)
    for res in geo_results:
        assert 35000 <= res["altitude"] <= 36500, f"GEO altitude {res['altitude']} km out of bounds (35000-36500 km)"
