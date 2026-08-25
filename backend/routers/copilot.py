import re
from datetime import datetime, timezone
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import ollama

from backend.db.connection import get_db
from backend.db.models import Satellite, ConjunctionEvent, ReentryAlert
from orbital_mechanics.solar_weather import fetch_aditya_l1_data

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    message: Optional[str] = None
    query: Optional[str] = None
    history: Optional[List[ChatMessage]] = []

def generate_offline_fallback(context_details: list, query: str) -> str:
    """
    Generates a structured, professional database-extracted report 
    when the local Llama 3.2 engine is offline.
    """
    if not context_details:
        return """### 📴 Offline Assistant Report
The local AI model (Llama 3.2) is currently offline or unreachable.

**Status:**
- No direct database records matching your query keywords were found.
- If you're asking about orbital mechanics theories or compliance rules, please activate the local LLM using `ollama run llama3.2` to enable natural language queries.
"""
    
    report_lines = [
        "### 📴 Offline Assistant Telemetry Report",
        "The local AI model (Llama 3.2) is currently unreachable. Extracting raw database telemetry directly to address your query:",
        ""
    ]
    
    for item in context_details:
        dtype = item.get("type")
        if dtype == "satellite":
            report_lines.extend([
                f"**🛰️ Satellite Status: {item['name']} (NORAD {item['norad_id']})**",
                f"- Operator: {item['operator']}",
                f"- Classification Type: {item['sat_type']}",
                f"- TLE Line 1: `{item['tle1']}`",
                f"- TLE Line 2: `{item['tle2']}`",
                ""
            ])
        elif dtype == "conjunction":
            report_lines.extend([
                f"**💥 Close Approach Alert: Conjunction ID {item['id']}**",
                f"- Primary NORAD: {item['primary_norad']}",
                f"- Secondary NORAD: {item['secondary_norad']}",
                f"- Miss Distance: {item['miss_distance']} km",
                f"- Time of Closest Approach (TCA): {item['tca']}",
                f"- Collision Probability (Pc): {item['pc']:.6e}",
                f"- Compliance Status: {item['compliance_status']}",
                ""
            ])
        elif dtype == "reentry":
            report_lines.extend([
                f"**☄️ Reentry Decay Alert: {item['name']} (NORAD {item['norad_id']})**",
                f"- Current Altitude: {item['current_altitude']} km",
                f"- Decay Rate: {item['decay_rate']} m/day",
                f"- Estimated Time of Reentry (ETA): {item['eta']}",
                f"- Spacecraft Survival Probability: {item['survival_pct']}%",
                f"- Ground Casualty Probability: {item['casualty_probability']:.2e}",
                ""
            ])
        elif dtype == "solar":
            report_lines.extend([
                "**☀️ Aditya-L1 Space Weather Report**",
                f"- Observed Solar Flux: {item['f10_7']} sfu",
                f"- Geomagnetic index Ap: {item['ap']}",
                f"- Active Flares: {item['active_flare']}",
                f"- CME Speed: {item['cme_speed']} km/s",
                f"- CME Progress: {item['cme_progress']}",
                f"- CME Impact State: {item['impact_active']}",
                ""
            ])
            
    report_lines.append("*Please restore local Ollama service to reactivate the natural language assistant.*")
    return "\n".join(report_lines)

@router.post("/chat")
async def copilot_chat(payload: ChatPayload, db: AsyncSession = Depends(get_db)):
    """
    RAG Chat endpoint. Searches the local database for keywords in the message,
    injects context, and queries Llama 3.2 locally.
    """
    query = (payload.query or payload.message or "").strip()
    history = payload.history or []
    
    # 1. Parse query and extract matching database contexts
    context_items = []
    
    # Match NORAD IDs (5 digit numbers)
    norad_matches = re.findall(r"\b\d{3,6}\b", query)
    
    # Check for general keywords
    query_lower = query.lower()
    is_conjunction_query = any(k in query_lower for k in ["conjunction", "collision", "hazard", "close approach"])
    is_reentry_query = any(k in query_lower for k in ["reentry", "decay", "fall", "burn"])
    is_solar_query = any(k in query_lower for k in ["solar", "weather", "aditya", "flare", "cme", "geomagnetic", "storm"])
    
    # A. Search Satellites table
    satellites_query = select(Satellite)
    res_sats = await db.execute(satellites_query)
    all_sats = res_sats.scalars().all()
    
    matched_sats = []
    for sat in all_sats:
        # Check if NORAD ID matches or name is in query
        if str(sat.norad_id) in norad_matches or sat.name.lower() in query_lower:
            matched_sats.append(sat)
            context_items.append({
                "type": "satellite",
                "norad_id": sat.norad_id,
                "name": sat.name,
                "operator": sat.operator,
                "sat_type": sat.type,
                "tle1": sat.tle1,
                "tle2": sat.tle2
            })
            
    # B. Search Conjunctions matching matched satellites or general query
    if matched_sats or is_conjunction_query:
        conj_query = select(ConjunctionEvent)
        res_conjs = await db.execute(conj_query)
        all_conjs = res_conjs.scalars().all()
        
        for conj in all_conjs:
            matched = False
            if is_conjunction_query:
                matched = True
            else:
                for sat in matched_sats:
                    if conj.primary_norad == sat.norad_id or conj.secondary_norad == sat.norad_id:
                        matched = True
                        break
            if matched:
                context_items.append({
                    "type": "conjunction",
                    "id": conj.id,
                    "primary_norad": conj.primary_norad,
                    "secondary_norad": conj.secondary_norad,
                    "miss_distance": conj.miss_distance,
                    "tca": conj.tca.isoformat() if conj.tca else None,
                    "pc": conj.pc,
                    "compliance_status": conj.compliance_status
                })
                
    # C. Search Reentry alerts
    if matched_sats or is_reentry_query:
        reentry_query = select(ReentryAlert)
        res_reentry = await db.execute(reentry_query)
        all_reentry = res_reentry.scalars().all()
        
        for alert in all_reentry:
            matched = False
            if is_reentry_query:
                matched = True
            else:
                for sat in matched_sats:
                    if alert.norad_id == sat.norad_id:
                        matched = True
                        break
            if matched:
                context_items.append({
                    "type": "reentry",
                    "norad_id": alert.norad_id,
                    "name": alert.name,
                    "current_altitude": alert.current_altitude,
                    "decay_rate": alert.decay_rate,
                    "eta": alert.eta.isoformat() if alert.eta else None,
                    "survival_pct": alert.survival_pct,
                    "casualty_probability": alert.casualty_probability
                })
                
    # D. Ingest Solar Weather
    if is_solar_query:
        try:
            aditya = fetch_aditya_l1_data(cache_path="solar_weather_cache.json")
            evt = aditya.get("active_event")
            context_items.append({
                "type": "solar",
                "f10_7": aditya["f10_7"],
                "ap": aditya["ap"],
                "active_flare": evt["flare_class"] if evt else "None",
                "cme_speed": evt["cme_speed"] if evt else 0.0,
                "cme_progress": f"{evt['cme_progress_pct']*100:.0f}%" if evt else "N/A",
                "impact_active": "Yes" if (evt and evt["impact_active"]) else "No"
            })
        except Exception:
            pass
            
    # Limit context size to avoid context bloat
    context_items = context_items[:5]
    
    # 2. Compile prompt context string
    context_str = ""
    if context_items:
        context_str = "DATABASE CONTEXT:\n" + "\n".join([str(item) for item in context_items])
        
    system_prompt = f"""You are ORVEXA Copilot, a secure, air-gapped space safety AI assistant.
You are running locally on the operator's machine.
The current UTC date and time is: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}.
Answer the user's questions professionally, focusing on orbital mechanics, collision risks, and satellite safety.
Use the DATABASE CONTEXT provided below to answer specific questions about satellite states.
If the database context is empty or doesn't address the query, use your general knowledge of space dynamics, but clarify that you are speaking generally.
Keep answers concise, markdown-formatted, and professional.
"""
    
    # 3. Format message history for Ollama
    ollama_messages = [
        {"role": "system", "content": f"{system_prompt}\n\n{context_str}"}
    ]
    # Add historical logs
    for h in history[-8:]: # keep last 8 turns of context
        ollama_messages.append({"role": h.role, "content": h.content})
    # Add current user query
    ollama_messages.append({"role": "user", "content": query})
    
    # 4. Call Local LLM via Ollama
    import socket
    ollama_online = False
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=2.0):
            ollama_online = True
    except Exception:
        ollama_online = False

    if ollama_online:
        try:
            client = ollama.Client(timeout=25.0)
            response = client.chat(
                model="llama3.2", 
                messages=ollama_messages,
                options={"num_predict": 200, "temperature": 0.3}
            )
            content = response["message"]["content"]
            return {"status": "success", "response": content, "mode": "online"}
        except Exception as e:
            print(f"Warning: local LLM (Ollama) unreachable or errored: {e}. Falling back to rule-based template.")
            fallback_content = generate_offline_fallback(context_items, query)
            return {"status": "success", "response": fallback_content, "mode": "offline"}
    else:
        fallback_content = generate_offline_fallback(context_items, query)
        return {"status": "success", "response": fallback_content, "mode": "offline"}
