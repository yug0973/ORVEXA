from typing import List, Dict
from datetime import datetime, timedelta, timezone
import json
from fastapi import APIRouter, HTTPException, Depends
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.connection import get_db
from backend.db.models import ReentryAlert, ConjunctionEvent, Satellite
from orbital_mechanics.solar_weather import (
    fetch_live_noaa_data,
    fetch_aditya_l1_data,
    trigger_aditya_flare,
    clear_aditya_flare
)

router = APIRouter(prefix="/api/solar", tags=["solar"])

@router.get("")
async def get_solar_weather():
    """
    Retrieves the current space weather parameters (observed F10.7 and Ap index),
    threat levels, and a 7-day historical trend.
    """
    # Fetch live or cached solar parameters (incorporating Aditya-L1 CME storm scaling)
    aditya_data = fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
    f10_7 = aditya_data["f10_7"]
    ap = aditya_data["ap"]
    
    # 1. Determine alert level based on index thresholds
    # F10.7: < 90 = Low, 90-150 = Moderate, 150-220 = High, > 220 = Severe
    # Ap: < 15 = Quiet, 15-30 = Active, 30-50 = Minor Storm, > 50 = Major Storm
    if f10_7 > 220.0 or ap > 50.0:
        alert_level = "Severe"
        description = "Extreme solar activity or major geomagnetic storm. Upper atmosphere heating is significantly increasing satellite drag."
    elif f10_7 > 150.0 or ap > 30.0:
        alert_level = "High"
        description = "Elevated solar activity. Orbital decay rates are accelerated."
    elif f10_7 > 90.0 or ap > 15.0:
        alert_level = "Moderate"
        description = "Moderate solar activity. Normal orbital decay progression."
    else:
        alert_level = "Low"
        description = "Quiet space weather. Baseline drag conditions apply."

    # 2. Synthesize a realistic 7-day historical trend for visualization
    # We add minor random fluctuations (normal distribution) around the current observed indices
    np.random.seed(int(aditya_data["timestamp"]) % 10000) # Seeding for deterministic trend per timestamp
    
    trend = []
    now = datetime.now()
    for i in reversed(range(7)):
        date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({
            "date": date_str,
            "f10_7": round(f10_7 + float(np.random.normal(0, 4.0)), 2),
            "ap": max(0.0, round(ap + float(np.random.normal(0, 2.0)), 2))
        })
        
    return {
        "f10_7": f10_7,
        "ap": ap,
        "drag_scaler": float(f10_7 / 70.0),
        "historical": trend,
        "current": {
            "f10_7": f10_7,
            "ap": ap,
            "updated_at": datetime.fromtimestamp(aditya_data["timestamp"])
        },
        "alert_metrics": {
            "level": alert_level,
            "description": description,
            "quiet_baseline_sfu": 70.0
        },
        "trend_history": trend
    }

@router.get("/aditya-l1")
async def get_aditya_l1():
    """
    Returns the real-time simulated SoLEXS & HEL1OS X-ray flux, CME propagation progress,
    and geomagnetic storm status.
    """
    try:
        return fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Aditya-L1 data: {e}")

@router.get("/forecast")
async def get_solar_forecast():
    """
    Retrieves the solar storm forecast threat levels and density multipliers.
    """
    aditya_data = fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
    active_event = aditya_data.get("active_event")
    
    overall_threat = "NORMAL"
    density_multiplier = 1.0
    
    if active_event and active_event.get("impact_active", False):
        fclass = active_event.get("flare_class", "C")
        if fclass == "X":
            overall_threat = "CRITICAL"
            density_multiplier = 3.5
        elif fclass == "M":
            overall_threat = "HIGH"
            density_multiplier = 1.8
        else:
            overall_threat = "MODERATE"
            density_multiplier = 1.2
            
    return {
        "overall_threat": overall_threat,
        "density_multiplier": density_multiplier,
        "f10_7": aditya_data.get("f10_7", 150.0),
        "ap": aditya_data.get("ap", 15.0)
    }

@router.post("/trigger-flare/{flare_class}")
async def trigger_flare(flare_class: str, db: AsyncSession = Depends(get_db)):
    """
    Manually triggers a simulated solar flare event of a specified class ('C', 'M', or 'X').
    Recalculates decay ETA and re-screens conjunctions for LEO satellites.
    """
    flare_class = flare_class.upper()
    if flare_class not in ["C", "M", "X"]:
        raise HTTPException(status_code=400, detail="Invalid flare class. Must be C, M, or X.")
    try:
        event = trigger_aditya_flare(flare_class)
        
        # Calculate multiplier
        if flare_class == "X":
            density_multiplier = 3.5
        elif flare_class == "M":
            density_multiplier = 1.8
        else:
            density_multiplier = 1.2
            
        # Re-run decay propagation for LEO satellites in ReentryAlert
        alerts_res = await db.execute(select(ReentryAlert))
        alerts = alerts_res.scalars().all()
        
        for alert in alerts:
            sat_res = await db.execute(select(Satellite).filter_by(norad_id=alert.norad_id))
            sat = sat_res.scalar_one_or_none()
            if sat:
                try:
                    from orbital_mechanics.monte_carlo_reentry import generate_reentry_corridor
                    corridor = generate_reentry_corridor(
                        sat.tle1, sat.tle2,
                        f10_7=event.get("f10_7", 150.0),
                        ap=event.get("ap", 15.0),
                        num_runs=20,
                        density_multiplier=density_multiplier
                    )
                    mean_decay_time_sec = corridor["properties"]["mean_decay_time_sec"]
                    alert.eta = datetime.now(timezone.utc) + timedelta(seconds=mean_decay_time_sec)
                    alert.corridor_geom = json.dumps(corridor["geometry"])
                except Exception as ex:
                    print(f"Error running decay propagation: {ex}")
                    # Fallback to manual scaling
                    base_offset = timedelta(days=2, hours=4) if alert.norad_id == 25544 else timedelta(days=3, hours=12)
                    alert.eta = datetime.now(timezone.utc) + base_offset / density_multiplier
                
                alert.decay_rate = round((12.45 if alert.norad_id == 25544 else 8.12) * density_multiplier, 2)
        
        # Create a new critical conjunction event
        # Delete if Cosmos debris conjunction already exists to avoid duplication
        await db.execute(ConjunctionEvent.__table__.delete().where(ConjunctionEvent.secondary_norad == 90002))
        
        storm_conj = ConjunctionEvent(
            primary_norad=25544,
            secondary_norad=90002,  # COSMOS 2251 DEBRIS
            tca=datetime.now(timezone.utc) + timedelta(hours=14),
            miss_distance=0.08, # in km
            radial=0.02,
            in_track=0.05,
            cross_track=-0.06,
            pc=4.82e-4, # Critical Pc
            covariance_matrix={
                "p_cov": [[0.04, 0.01, 0.0], [0.01, 0.06, 0.0], [0.0, 0.0, 0.02]],
                "s_cov": [[0.03, 0.0, 0.0], [0.0, 0.05, 0.0], [0.0, 0.0, 0.01]]
            },
            compliance_status="Compliance Required"
        )
        db.add(storm_conj)
        await db.commit()
        
        # Broadcast alert to all WebSocket clients
        from backend.routers.ws_swarm import broadcast_alert
        await broadcast_alert({
            "event": "solar_storm_rescreen",
            "toast": f"Solar storm forecast — {len(alerts)} satellites re-screened, 1 new conjunction detected."
        })
        
        return {"status": "success", "triggered_event": event}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to trigger solar flare: {e}")

@router.post("/clear-flare")
async def clear_flare(db: AsyncSession = Depends(get_db)):
    """
    Clears any active simulated flare events and resets reentry alert parameters.
    """
    try:
        clear_aditya_flare()
        
        # Reset Reentry Alerts to quiet baselines
        alerts_res = await db.execute(select(ReentryAlert))
        alerts = alerts_res.scalars().all()
        
        for alert in alerts:
            if alert.norad_id == 25544:
                alert.decay_rate = 12.45
                alert.eta = datetime.now(timezone.utc) + timedelta(days=2, hours=4)
            else:
                alert.decay_rate = 8.12
                alert.eta = datetime.now(timezone.utc) + timedelta(days=3, hours=12)
                
        # Delete the storm conjunction
        await db.execute(ConjunctionEvent.__table__.delete().where(ConjunctionEvent.secondary_norad == 90002))
        await db.commit()
        
        # Broadcast reset
        from backend.routers.ws_swarm import broadcast_alert
        await broadcast_alert({
            "event": "solar_storm_cleared",
            "toast": "Solar storm cleared. Satellite trajectories and decay rates restored to quiet baseline."
        })
        
        return {"status": "success", "detail": "Active solar flares cleared and orbits restored."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear solar flare: {e}")
