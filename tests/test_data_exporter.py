import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orbital_mechanics.data_exporter import run_pipeline_and_export, Satellite, StateVector, ConjunctionEvent, ReentryAlert, Base

def test_data_exporter_pipeline():
    """
    Integration test to execute the full pipeline and verify table creation,
    conjunction calculations, and database population using a local test SQLite db.
    """
    test_db_file = "test_ORVEXA.db"
    
    # Clean up test database if it exists
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
        
    test_db_url = f"sqlite:///{test_db_file}"
    
    # Inject DATABASE_URL into environment for data_exporter
    os.environ["DATABASE_URL"] = test_db_url
    
    try:
        # Run the full pipeline
        run_pipeline_and_export()
        
        # Connect to test db and verify records exist
        engine = create_engine(test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 1. Assert satellites table is populated
        sats = session.query(Satellite).all()
        assert len(sats) == 100  # Should be our test subset limit
        assert sats[0].norad_id > 0
        assert sats[0].tle_line1 != ""
        assert sats[0].tle_line2 != ""
        
        # 2. Assert state_vectors table is populated
        svs = session.query(StateVector).all()
        assert len(svs) > 0
        assert svs[0].position_x != 0.0
        
        # 3. Assert conjunction_events table is populated
        conjs = session.query(ConjunctionEvent).all()
        assert len(conjs) > 0
        assert conjs[0].primary_id in [s.norad_id for s in sats]
        # Verify RIC coordinates are set
        assert conjs[0].radial is not None
        assert conjs[0].in_track is not None
        assert conjs[0].cross_track is not None
        
        # 4. Assert reentry_alerts table is populated (demo candidate CALSPHERE 1)
        alerts = session.query(ReentryAlert).all()
        assert len(alerts) > 0
        assert alerts[0].name == "CALSPHERE 1"
        assert alerts[0].corridor_geojson != ""
        
        # Verify GeoJSON format in reentry alert
        import json
        geojson = json.loads(alerts[0].corridor_geojson)
        assert geojson["type"] == "Feature"
        assert geojson["geometry"]["type"] == "MultiPolygon"
        
        print("\nAll pipeline integration assertions passed!")
        session.close()
        
    finally:
        # Clean up database file
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass
        # Clean up env var
        os.environ.pop("DATABASE_URL", None)
