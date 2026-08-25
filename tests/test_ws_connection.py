import os
import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

# Configure dynamic database environment for routers/models import
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_ws.db"

from backend.main import app

client = TestClient(app)

def test_websocket_swarm_run_streaming():
    """
    Test WebSocket connection and log delivery.
    Connects to /api/ws/swarm/run, receives sequential agent logs,
    verifies structure, progress percentage, and clean termination.
    """
    # 1. Establish WebSocket connection
    with client.websocket_connect("/api/ws/swarm/run") as websocket:
        logs = []
        
        # 2. Progressively read incoming JSON log frames
        while True:
            try:
                data = websocket.receive_json()
                logs.append(data)
                
                # Check log frame data structure
                assert "percentage" in data
                assert "agent" in data
                assert "log" in data
                assert "timestamp" in data
                
                assert isinstance(data["percentage"], int)
                assert isinstance(data["agent"], str)
                assert isinstance(data["log"], str)
                
                if data.get("percentage") == 100:
                    break
            except WebSocketDisconnect:
                # Expected clean close at the end of streaming
                break
            except Exception as e:
                # Handle client-side socket reading close signatures
                if "was already closed" in str(e) or "handshake" in str(e):
                    break
                raise e

        # 3. Assert sequential steps completed successfully
        assert len(logs) >= 6  # At least 6 sequential pipeline steps
        
        # Verify first step properties
        assert logs[0]["percentage"] == 10
        assert logs[0]["agent"] == "DATA_INGESTION_AGENT"
        
        # Verify final step properties
        last_log = logs[-1]
        assert last_log["percentage"] == 100
        assert last_log["agent"] == "COMPLIANCE_AGENT"
        assert "complete" in last_log["log"].lower()
        
        # Verify progression ordering
        for i in range(1, len(logs)):
            assert logs[i]["percentage"] >= logs[i-1]["percentage"]
            
        print("\nWebSocket swarm streaming tests passed successfully!")
