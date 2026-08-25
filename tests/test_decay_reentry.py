import pytest
from datetime import datetime, timezone
import numpy as np
from orbital_mechanics.decay_engine import get_atmospheric_density
from orbital_mechanics.monte_carlo_reentry import generate_reentry_corridor

def test_atmospheric_density_solar_storm_spike():
    """
    Assert that atmospheric density increases as solar flux (F10.7) increases.
    """
    dt = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    alt = 300.0  # 300 km altitude (sensitive to solar activity)
    
    # Solar Minimum
    rho_min = get_atmospheric_density(dt, alt, 0.0, 0.0, 70.0, 70.0, 15.0)
    
    # Solar Storm / Solar Maximum
    rho_max = get_atmospheric_density(dt, alt, 0.0, 0.0, 250.0, 250.0, 15.0)
    
    # Density should be significantly higher during solar maximum
    assert rho_max > rho_min
    print(f"\nDensity Spike: Solar Min = {rho_min:.6e} kg/m^3 | Solar Max = {rho_max:.6e} kg/m^3")

def test_decay_time_decreases_with_density_spike():
    """
    Assert that the numerical decay time decreases as atmospheric density spikes.
    Use generate_reentry_corridor with different F10.7 values and check mean decay time.
    """
    line1 = "1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998"
    line2 = "2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408"
    
    # Run with 20 particles to keep test execution fast
    # Case 1: Low solar activity (F10.7 = 70.0) -> slow decay
    res_low = generate_reentry_corridor(line1, line2, f10_7=70.0, ap=15.0, num_runs=20)
    decay_time_low = res_low["properties"]["mean_decay_time_sec"]
    
    # Case 2: High solar activity (F10.7 = 300.0) -> rapid decay due to atmospheric heating and expansion
    res_high = generate_reentry_corridor(line1, line2, f10_7=300.0, ap=15.0, num_runs=20)
    decay_time_high = res_high["properties"]["mean_decay_time_sec"]
    
    # High solar flux = higher density = faster decay = lower decay time
    assert decay_time_high < decay_time_low
    print(f"\nDecay Time: Low Activity = {decay_time_low:.1f}s | High Activity = {decay_time_high:.1f}s")

def test_reentry_corridor_geojson_format():
    """
    Verify that generate_reentry_corridor returns a valid GeoJSON MultiPolygon feature.
    """
    line1 = "1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998"
    line2 = "2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408"
    
    corridor = generate_reentry_corridor(line1, line2, f10_7=150.0, ap=15.0, num_runs=30)
    
    assert corridor["type"] == "Feature"
    assert "geometry" in corridor
    assert corridor["geometry"]["type"] == "MultiPolygon"
    assert "coordinates" in corridor["geometry"]
    
    # Coordinates format: List of polygons -> List of rings -> List of coords [lon, lat]
    coords = corridor["geometry"]["coordinates"]
    assert len(coords) > 0  # At least one polygon
    assert len(coords[0]) > 0  # At least one ring (outer boundary)
    assert len(coords[0][0]) >= 4  # Convex hull has at least 3 vertices + closed loop first vertex
    
    # Properties checks
    props = corridor["properties"]
    assert props["norad_id"] == 25544
    assert props["satellite_name"] == "SATELLITE"
    assert props["simulated_points"] == 30
    assert "mean_decay_time_sec" in props
