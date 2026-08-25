from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

import asyncio
from backend.services.swarm_orchestrator import SwarmOrchestrator

router = APIRouter(tags=["swarm-ws"])

@router.websocket("/api/ws/swarm/run")
async def ws_run_swarm(websocket: WebSocket):
    """
    WebSocket endpoint that initiates the AI Swarm Orchestrator safety pipeline
    and streams progressive execution logs (JSON text frames) to the client.
    """
    await websocket.accept()
    await asyncio.sleep(0.01)
    orchestrator = SwarmOrchestrator()
    
    try:
        # Run pipeline limiting to 10 satellites for fast verification
        async for log_frame in orchestrator.run_pipeline(limit_sats=10):
            # Stream the progression log frame as JSON text
            await websocket.send_json(log_frame)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected from swarm execution.")
    except Exception as e:
        print(f"Error during Swarm WebSocket streaming: {e}")
        try:
            await websocket.send_json({
                "percentage": 100,
                "agent": "SYSTEM",
                "log": f"Execution interrupted by server error: {e}",
                "timestamp": ""
            })
        except Exception:
            pass
    finally:
        # Cleanly close the WebSocket connection if it remains open
        try:
            await websocket.close()
        except Exception:
            pass

active_connections: list[WebSocket] = []

@router.websocket("/api/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """
    WebSocket endpoint that streams real-time space safety alerts and notifications.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Receive text to keep connection alive or handle client heartbeats
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_alert(message: dict):
    """
    Utility function to broadcast a message to all active alert WebSocket connections.
    """
    disconnected_sockets = []
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected_sockets.append(ws)
            
    for ws in disconnected_sockets:
        if ws in active_connections:
            active_connections.remove(ws)
