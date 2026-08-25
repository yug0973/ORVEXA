import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.wkt import loads as load_wkt
from shapely.geometry import mapping

try:
    from geoalchemy2.shape import to_shape
    GEOALCHEMY_AVAILABLE = True
except ImportError:
    GEOALCHEMY_AVAILABLE = False

from backend.db.connection import get_db
from backend.db.models import ReentryAlert
from orbital_mechanics.solar_weather import fetch_aditya_l1_data

router = APIRouter(prefix="/api/reentry", tags=["reentry"])

def parse_corridor_to_geojson_geometry(geom_col) -> Optional[dict]:
    """
    Helper function to parse spatial database columns (WKT, GeoJSON, or WKBElements) 
    into standard Python dictionary GeoJSON coordinates format.
    """
    if not geom_col:
        return None
        
    # Check if SQLite fallback is active (the geometry column will be a plain string)
    if isinstance(geom_col, str):
        # 1. Check if the string is already a GeoJSON string
        try:
            # If it's a full GeoJSON feature, extract geometry
            data = json.loads(geom_col)
            if isinstance(data, dict):
                if "geometry" in data:
                    return data["geometry"]
                return data
        except json.JSONDecodeError:
            pass
            
        # 2. Check if the string is a WKT string
        try:
            poly = load_wkt(geom_col)
            return mapping(poly)
        except Exception:
            pass
            
        return None

    # PostgreSQL / PostGIS geometry (represented as WKBElement or similar)
    if GEOALCHEMY_AVAILABLE:
        try:
            poly = to_shape(geom_col)
            return mapping(poly)
        except Exception as e:
            print(f"Error converting PostGIS WKBElement using geoalchemy2: {e}")
            
    return None

@router.get("")
async def get_reentry_alerts(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all space objects designated as active reentry decay candidates 
    (altitude < 250 km) along with their estimated decay times and survival risks.
    """
    query = select(ReentryAlert).order_by(ReentryAlert.eta.asc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Fetch active storm status to apply real-time scaling
    storm_multiplier = 1.0
    impact_active = False
    try:
        aditya_data = fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
        active_event = aditya_data.get("active_event")
        if active_event and active_event.get("impact_active", False):
            impact_active = True
            fclass = active_event["flare_class"]
            if fclass == "X":
                storm_multiplier = 3.5
            elif fclass == "M":
                storm_multiplier = 1.8
            else:
                storm_multiplier = 1.2
    except Exception as e:
        print(f"Error fetching solar forecast in reentry router: {e}")
        
    from datetime import datetime, timezone
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    
    response_alerts = []
    for alert in alerts:
        # Scale decay rate
        decay_rate = round(alert.decay_rate * storm_multiplier, 2)
        
        # Calculate dynamic ETA adjustment
        eta = alert.eta
        if impact_active and alert.eta:
            if alert.eta > now_dt:
                rem = alert.eta - now_dt
                eta = now_dt + rem / storm_multiplier
                
        response_alerts.append({
            "norad_id": alert.norad_id,
            "name": alert.name,
            "current_altitude": alert.current_altitude,
            "decay_rate": decay_rate,
            "eta": eta,
            "uncertainty_hours": round(alert.uncertainty_hours * (1.2 if impact_active else 1.0), 1),
            "survival_pct": alert.survival_pct,
            "casualty_probability": alert.casualty_probability,
            "storm_multiplier": storm_multiplier if impact_active else 1.0
        })
        
    return response_alerts

@router.get("/{norad_id}/map")
async def get_reentry_corridor_map(norad_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the simulated landing corridor (uncertainty ellipse/hull) for a decaying 
    object formatted as a standard GeoJSON FeatureCollection for map rendering.
    """
    query = select(ReentryAlert).filter_by(norad_id=norad_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Reentry alert for NORAD {norad_id} not found.")

    geom_geojson = parse_corridor_to_geojson_geometry(alert.corridor_geom)
    if not geom_geojson:
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse landing corridor geometry from database."
        )

    # Format as a complete GeoJSON FeatureCollection
    geojson_feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geom_geojson,
                "properties": {
                    "norad_id": alert.norad_id,
                    "name": alert.name,
                    "decay_rate": alert.decay_rate,
                    "eta": alert.eta.isoformat() if alert.eta else None,
                    "uncertainty_hours": alert.uncertainty_hours,
                    "survival_pct": alert.survival_pct,
                    "casualty_probability": alert.casualty_probability
                }
            }
        ]
    }
    
    return geojson_feature_collection
