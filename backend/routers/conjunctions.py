import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.connection import get_db
from backend.db.models import ConjunctionEvent, Satellite

router = APIRouter(prefix="/api/conjunctions", tags=["conjunctions"])

@router.get("")
async def get_conjunctions(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all active conjunction events (close approaches) sorted by 
    collision probability (Pc) descending (highest hazard level first).
    """
    # Query conjunction events sorted by Pc descending
    query = select(ConjunctionEvent).order_by(ConjunctionEvent.pc.desc())
    result = await db.execute(query)
    events = result.scalars().all()
    
    # We want to resolve names of primary and secondary satellites as well.
    # To keep it efficient, we resolve them in one go or map after.
    # A quick way is to query names for norad_ids.
    norad_ids = set()
    for ev in events:
        norad_ids.add(ev.primary_norad)
        norad_ids.add(ev.secondary_norad)
        
    names_map = {}
    if norad_ids:
        sats_result = await db.execute(select(Satellite).where(Satellite.norad_id.in_(list(norad_ids))))
        for sat in sats_result.scalars().all():
            names_map[sat.norad_id] = sat.name

    return [
        {
            "id": ev.id,
            "primary_norad": ev.primary_norad,
            "primary_name": names_map.get(ev.primary_norad, "Unknown"),
            "secondary_norad": ev.secondary_norad,
            "secondary_name": names_map.get(ev.secondary_norad, "Unknown"),
            "tca": ev.tca,
            "miss_distance": ev.miss_distance,
            "pc": ev.pc,
            "compliance_status": ev.compliance_status
        }
        for ev in events
    ]

@router.get("/{event_id}")
async def get_conjunction_details(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves complete details of a specific conjunction event.
    Returns relative positions (Radial, In-track, Cross-track) and 
    uncertainty covariance matrices.
    """
    # Fetch event by ID
    query = select(ConjunctionEvent).filter_by(id=event_id)
    result = await db.execute(query)
    ev = result.scalar_one_or_none()
    
    if not ev:
        raise HTTPException(status_code=404, detail=f"Conjunction event with ID {event_id} not found.")

    # Fetch satellite objects
    p_result = await db.execute(select(Satellite).filter_by(norad_id=ev.primary_norad))
    primary = p_result.scalar_one_or_none()
    s_result = await db.execute(select(Satellite).filter_by(norad_id=ev.secondary_norad))
    secondary = s_result.scalar_one_or_none()

    # Parse covariance matrix JSON
    covariance_matrix = None
    if ev.covariance_matrix:
        if isinstance(ev.covariance_matrix, str):
            try:
                covariance_matrix = json.loads(ev.covariance_matrix)
            except json.JSONDecodeError:
                covariance_matrix = ev.covariance_matrix
        else:
            covariance_matrix = ev.covariance_matrix

    # 5. Compute explainable Pc metrics
    explain_data = None
    if primary and secondary and primary.tle1 and primary.tle2 and secondary.tle1 and secondary.tle2:
        try:
            from datetime import timezone
            from skyfield.api import load, EarthSatellite
            from orbital_mechanics.data_exporter import generate_realistic_covariance
            from orbital_mechanics.chan_pc import calculate_chan_pc_detailed
            
            ts = load.timescale(builtin=True)
            sat_p = EarthSatellite(primary.tle1, primary.tle2, primary.name, ts)
            sat_s = EarthSatellite(secondary.tle1, secondary.tle2, secondary.name, ts)
            
            tca_utc = ev.tca
            if tca_utc.tzinfo is None:
                tca_utc = tca_utc.replace(tzinfo=timezone.utc)
            else:
                tca_utc = tca_utc.astimezone(timezone.utc)
                
            t_sf = ts.from_datetime(tca_utc)
            g_p = sat_p.at(t_sf)
            g_s = sat_s.at(t_sf)
            
            p_state = (g_p.position.km.tolist(), g_p.velocity.km_per_s.tolist())
            s_state = (g_s.position.km.tolist(), g_s.velocity.km_per_s.tolist())
            
            p_cov = covariance_matrix.get("p_cov") if (covariance_matrix and isinstance(covariance_matrix, dict)) else None
            s_cov = covariance_matrix.get("s_cov") if (covariance_matrix and isinstance(covariance_matrix, dict)) else None
            
            if not p_cov or not s_cov:
                p_cov = generate_realistic_covariance(p_state[0], p_state[1]).tolist()
                s_cov = generate_realistic_covariance(s_state[0], s_state[1]).tolist()
                
            detailed_res = calculate_chan_pc_detailed(p_state, s_state, p_cov, s_cov, hbr=10.0)
            explain_data = {
                "miss_distance_km": detailed_res["miss_distance_km"],
                "sigma_major": detailed_res["sigma_major"],
                "sigma_minor": detailed_res["sigma_minor"],
                "pc_terms": {
                    "u": detailed_res["u"],
                    "alpha": detailed_res["alpha"],
                    "beta": detailed_res["beta"]
                }
            }
        except Exception as ex:
            print(f"Error computing explainable Pc: {ex}")

    return {
        "id": ev.id,
        "primary": {
            "norad_id": ev.primary_norad,
            "name": primary.name if primary else "Unknown",
            "operator": primary.operator if primary else "Unknown"
        },
        "secondary": {
            "norad_id": ev.secondary_norad,
            "name": secondary.name if secondary else "Unknown",
            "operator": secondary.operator if secondary else "Unknown"
        },
        "tca": ev.tca,
        "miss_distance": ev.miss_distance,
        "relative_vectors": {
            "radial": ev.radial,
            "in_track": ev.in_track,
            "cross_track": ev.cross_track
        },
        "pc": ev.pc,
        "covariance_matrix": covariance_matrix,
        "compliance_status": ev.compliance_status,
        "explain": explain_data
    }

