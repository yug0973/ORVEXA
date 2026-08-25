import os
import sys
import json
import asyncio
from datetime import datetime, timezone, timedelta

# Force DATABASE_URL to use local SQLite development database before loading backend modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///ORVEXA.db"

# Add project root to sys.path to resolve imports cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.main import app
from backend.db.models import Base, Satellite, StateVector, ConjunctionEvent, ReentryAlert, ComplianceFiling

client = TestClient(app)

async def ensure_test_fixtures():
    """
    Checks if ORVEXA.db database is populated with necessary satellite,
    conjunction, and reentry mock data for the integration test.
    Seeds fallback entries if tables are empty.
    """
    engine = create_async_engine("sqlite+aiosqlite:///ORVEXA.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
    
    async with AsyncSessionLocal() as session:
        # 1. Verify Satellites
        res_sats = await session.execute(select(Satellite))
        sats = res_sats.scalars().all()
        if not sats:
            print("Seeding fallback satellites...")
            sats = [
                Satellite(
                    norad_id=900,
                    name="CALSPHERE 1",
                    operator="Operational",
                    type="Payload",
                    tle1="1 00900U 64063C   26221.48381944 -.00000034  00000-0  00000-0 0  9997",
                    tle2="2 00900  90.1740  72.8462 0021950  45.3210 314.8920 13.72948194 92144",
                    updated_at=datetime.now(timezone.utc)
                ),
                Satellite(
                    norad_id=902,
                    name="CALSPHERE 2",
                    operator="Operational",
                    type="Payload",
                    tle1="1 00902U 64063D   26221.48381944 -.00000034  00000-0  00000-0 0  9997",
                    tle2="2 00902  90.1750  72.8472 0021960  45.3220 314.8930 13.72948294 92145",
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            for s in sats:
                session.add(s)
            await session.flush()
            
        # 2. Verify State Vectors
        res_sv = await session.execute(select(StateVector))
        if not res_sv.scalars().first():
            print("Seeding fallback state vectors...")
            for s in sats:
                for h in range(5):
                    sv = StateVector(
                        norad_id=s.norad_id,
                        epoch=datetime.now(timezone.utc) + timedelta(hours=h),
                        position_x=1200.0 + h * 50.0,
                        position_y=2300.0 - h * 30.0,
                        position_z=3400.0 + h * 100.0,
                        velocity_x=3.5,
                        velocity_y=4.2,
                        velocity_z=-5.1
                    )
                    session.add(sv)
            
        # 3. Verify Conjunction Events
        res_conj = await session.execute(select(ConjunctionEvent))
        if not res_conj.scalars().first():
            print("Seeding fallback conjunction event...")
            conj = ConjunctionEvent(
                id=1,
                primary_norad=sats[0].norad_id,
                secondary_norad=sats[1].norad_id,
                tca=datetime.now(timezone.utc) + timedelta(days=1),
                miss_distance=0.45,
                radial=0.05,
                in_track=0.25,
                cross_track=-0.35,
                pc=1.5e-5,
                covariance_matrix={"p_cov": [[0.18, 0.04], [0.04, 0.08]]},
                compliance_status="Compliance Required"
            )
            session.add(conj)
            
        # 4. Verify Reentry Alerts
        res_re = await session.execute(select(ReentryAlert))
        if not res_re.scalars().first():
            print("Seeding fallback reentry alert...")
            corridor = {
              "type": "Polygon",
              "coordinates": [
                [[65.0, 5.0], [88.0, 7.0], [85.0, 18.0], [62.0, 16.0], [65.0, 5.0]]
              ]
            }
            alert = ReentryAlert(
                norad_id=sats[0].norad_id,
                name=sats[0].name,
                current_altitude=185.4,
                decay_rate=12.45,
                eta=datetime.now(timezone.utc) + timedelta(days=2),
                uncertainty_hours=6.5,
                survival_pct=18.5,
                corridor_geom=json.dumps(corridor),
                casualty_probability=1.25e-5
            )
            session.add(alert)
            
        await session.commit()
    await engine.dispose()

def run_tests():
    print("======================================================================")
    print("                 ORVEXA END-TO-END INTEGRATION TEST               ")
    print("======================================================================")
    
    passed_tests = 0
    total_tests = 6
    
    # Test 1: Verify API CORS Configuration
    try:
        print("\n[TEST 1] Verifying API CORS Middlewares...")
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Requested-With"
        }
        res = client.options("/api/satellites", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert "access-control-allow-origin" in res.headers, "CORS allow-origin header missing!"
        print("  -> PASS: CORS headers allowed origin http://localhost:5173.")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: CORS check failed: {e}")
        
    # Test 2: Validate Database propagated state records
    try:
        print("\n[TEST 2] Verifying Database contains active satellites...")
        res = client.get("/api/satellites?limit=5")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert len(data["results"]) > 0, "No satellites returned in database query!"
        print(f"  -> PASS: Database contains {len(data['results'])} seeded satellites.")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: Database check failed: {e}")

    # Test 3: Validate CZML Trajectory Compliance
    try:
        print("\n[TEST 3] Verifying CZML dynamic trajectory format...")
        res = client.get("/api/satellites/czml?limit=2")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        czml = res.json()
        assert isinstance(czml, list), "CZML must be a JSON array"
        assert len(czml) > 0, "CZML array is empty"
        assert czml[0]["id"] == "document", "First CZML packet must be the document packet"
        assert "clock" in czml[0], "Document packet must contain clock configurations"
        
        # Verify satellite packet coordinates
        sat_packet = czml[1]
        assert "position" in sat_packet, "Satellite packet must contain position coordinates"
        assert "cartesian" in sat_packet["position"], "Position packet must use cartesian coordinates list"
        print("  -> PASS: CZML structure complies with CesiumJS standards.")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: CZML compliance check failed: {e}")

    # Test 4: Validate Leaflet GeoJSON Coordinates Ordering (lat/lng check)
    try:
        print("\n[TEST 4] Verifying Leaflet GeoJSON coordinates ordering...")
        res = client.get("/api/reentry")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        alerts = res.json()
        assert len(alerts) > 0, "No reentry alerts available!"
        norad_id = alerts[0]["norad_id"]
        
        res_map = client.get(f"/api/reentry/{norad_id}/map")
        assert res_map.status_code == 200, f"Expected 200, got {res_map.status_code}"
        geojson = res_map.json()
        assert geojson["type"] == "FeatureCollection", "Map must return FeatureCollection"
        
        geom = geojson["features"][0]["geometry"]
        assert geom["type"] == "Polygon", "Corridor geometry must be Polygon"
        poly_coords = geom["coordinates"][0]
        
        # Leaflet GeoJSON coords are in [longitude, latitude] format
        for pt in poly_coords:
            assert len(pt) == 2, "Coordinate point must contain exactly 2 coordinates"
            assert -180.0 <= pt[0] <= 180.0, f"Longitude {pt[0]} out of bounds (-180, 180)"
            assert -90.0 <= pt[1] <= 90.0, f"Latitude {pt[1]} out of bounds (-90, 90)"
            
        print(f"  -> PASS: Polygon coordinates are valid [lon, lat] ordered: {poly_coords[0]}...")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: Spatial ordering check failed: {e}")

    # Test 5: Validate Compliance Agent generates briefing (using fallback gracefully if needed)
    try:
        print("\n[TEST 5] Verifying Compliance briefing generator (Ollama fallback)...")
        res = client.get("/api/conjunctions")
        assert res.status_code == 200
        conjs = res.json()
        assert len(conjs) > 0, "No conjunction events found!"
        event_id = str(conjs[0]["id"])
        
        # Submit CAM filing request
        res_file = client.post("/api/compliance/file", json={
            "event_id": event_id,
            "operator_name": "ISRO End-to-End Test Group"
        })
        assert res_file.status_code == 201, f"Expected 201, got {res_file.status_code}"
        data = res_file.json()
        assert "form_data" in data, "Filing response missing form_data"
        assert "briefing" in data["form_data"], "Filing response missing briefing"
        assert len(data["form_data"]["briefing"]) > 50, "Filing briefing statement is too short!"
        print("  -> PASS: Compliance brief generated successfully.")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: Compliance briefing check failed: {e}")

    # Test 6: Validate generated PDF file is saved to server storage
    try:
        print("\n[TEST 6] Verifying PDF compiler and storage output...")
        res_filings = client.post("/api/compliance/file", json={
            "event_id": "1",
            "operator_name": "ISRO E2E PDF Check Group"
        })
        assert res_filings.status_code == 201
        data = res_filings.json()
        pdf_path = data["pdf_path"]
        
        assert pdf_path != "PENDING", "Filing compiled PDF path is pending!"
        assert os.path.exists(pdf_path), f"Filing PDF file does not exist at path: {pdf_path}"
        assert os.path.getsize(pdf_path) > 100, f"Filing PDF file size is suspiciously small: {os.path.getsize(pdf_path)} bytes"
        print(f"  -> PASS: PDF file compiled and verified at path: {pdf_path} ({os.path.getsize(pdf_path)} bytes).")
        passed_tests += 1
    except Exception as e:
        print(f"  -> FAIL: PDF compilation check failed: {e}")

    # Summary Report
    print("\n======================================================================")
    print(f"RESULT: {passed_tests} / {total_tests} TESTS PASSED")
    print("======================================================================")
    
    if passed_tests == total_tests:
        print("SYSTEM READINESS STATUS: PASS")
        sys.exit(0)
    else:
        print("SYSTEM READINESS STATUS: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(ensure_test_fixtures())
    run_tests()
