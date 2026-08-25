import pytest
from orbital_mechanics.solar_weather import fetch_live_noaa_data, get_drag_coefficient_scaler

def test_fetch_live_noaa_data():
    """
    Verify that NOAA data fetching works and outputs are parsed correctly as floats.
    """
    data = fetch_live_noaa_data(cache_path="solar_weather_cache.json")
    
    assert isinstance(data, dict)
    assert "f10_7" in data
    assert "ap" in data
    assert "timestamp" in data
    
    # Assert values are float type
    assert isinstance(data["f10_7"], float)
    assert isinstance(data["ap"], float)
    
    # Assert values are within physically sensible ranges
    assert 50.0 <= data["f10_7"] <= 400.0  # F10.7 ranges from quiet sun (~65) to solar storm (>300)
    assert 0.0 <= data["ap"] <= 400.0      # Ap ranges from quiet (0) to extreme geomagnetic storm (>200)

def test_drag_coefficient_scaler():
    """
    Verify the drag coefficient scaler returns the correct ratio relative to quiet sun (70 sfu).
    """
    # Quiet Sun: scaler = 70 / 70 = 1.0
    assert get_drag_coefficient_scaler(70.0) == pytest.approx(1.0)
    
    # Solar Storm: scaler = 280 / 70 = 4.0
    assert get_drag_coefficient_scaler(280.0) == pytest.approx(4.0)
    
    # Typical Sun: scaler = 140 / 70 = 2.0
    assert get_drag_coefficient_scaler(140.0) == pytest.approx(2.0)

def test_fetch_aditya_l1_data():
    """
    Verify that the simulated Aditya-L1 observations yield the correct structure and sensible values.
    """
    from orbital_mechanics.solar_weather import fetch_aditya_l1_data
    
    data = fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
    
    assert isinstance(data, dict)
    assert "timestamp" in data
    assert "solexs_flux" in data
    assert "hel1os_flux" in data
    assert "f10_7" in data
    assert "ap" in data
    
    assert isinstance(data["solexs_flux"], float)
    assert isinstance(data["hel1os_flux"], float)
    assert 0.0 < data["solexs_flux"] < 1.0  # W/m^2 range (very small floats)
    assert data["hel1os_flux"] >= 0.0

def test_trigger_and_clear_aditya_flare():
    """
    Verify that triggering a simulated flare writes the parameters correctly,
    impacts the aditya telemetry feed, and can be successfully cleared.
    """
    import os
    import time
    from orbital_mechanics.solar_weather import fetch_aditya_l1_data, trigger_aditya_flare, clear_aditya_flare
    
    trigger_file = "test_aditya_trigger.json"
    
    # 1. Trigger an X-class flare
    event = trigger_aditya_flare("X", trigger_path=trigger_file)
    assert event["flare_class"] == "X"
    assert event["cme_speed"] == 1800.0
    assert os.path.exists(trigger_file)
    
    # 2. Check that the telemetries reflect the active flare
    data = fetch_aditya_l1_data(cache_path="solar_weather_cache.json", trigger_path=trigger_file)
    assert data["active_event"] is not None
    assert data["active_event"]["flare_class"] == "X"
    assert data["active_event"]["cme_speed"] == 1800.0
    
    # 3. Clear the active flare
    clear_aditya_flare(trigger_path=trigger_file)
    assert not os.path.exists(trigger_file)
    
    # 4. Check that event is no longer active (or falls back to auto if in window)
    data_cleared = fetch_aditya_l1_data(cache_path="solar_weather_cache.json", trigger_path=trigger_file)
    # The default auto flare is C-class if it triggers, so if it's not None, it shouldn't be X
    if data_cleared["active_event"]:
        assert data_cleared["active_event"]["flare_class"] != "X"

