"""
FastAPI backend server
Exposes the drone security agent via REST API for the frontend dashboard
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from typing import Optional, AsyncGenerator
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from mock_data import SIMULATED_FRAMES, TELEMETRY_DATA
from frame_index import FrameIndex
from services.agent import (
    analyze_frame_with_ai, generate_daily_summary, run_supervisor
)

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="Drone Security Analyst API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
patrol_index = FrameIndex()
patrol_complete = False
patrol_running = False


class QuestionRequest(BaseModel):
    question: str
    target_agent: Optional[str] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/frames")
def get_frames():
    """Return all indexed frames."""
    return {"frames": patrol_index.frames}


@app.get("/api/alerts")
def get_alerts():
    """Return all generated alerts."""
    return {"alerts": patrol_index.alerts}


@app.get("/api/events")
def get_events():
    """Return the event log."""
    return {"events": patrol_index.event_log}


@app.get("/api/stats")
def get_stats():
    """Return summary statistics."""
    return patrol_index.get_summary_stats()


@app.get("/api/query/object/{object_type}")
def query_by_object(object_type: str):
    """Query frames by detected object."""
    results = patrol_index.query_by_object(object_type)
    return {"query": object_type, "results": results, "count": len(results)}


@app.get("/api/query/location/{location}")
def query_by_location(location: str):
    results = patrol_index.query_by_location(location)
    return {"query": location, "results": results, "count": len(results)}


@app.get("/api/query/threat/{level}")
def query_by_threat(level: str):
    results = patrol_index.query_by_threat_level(level)
    return {"query": level, "results": results, "count": len(results)}


@app.post("/api/ask")
def ask_question(req: QuestionRequest):
    """Answer a follow-up question about the patrol."""
    if not patrol_index.frames:
        raise HTTPException(status_code=400, detail="No patrol data available yet.")
    try:
        answer = run_supervisor(req.question, patrol_index, target_agent=req.target_agent)
        return {"question": req.question, "answer": answer}
    except Exception as e:
        print(f"\n[ERROR] /api/ask Failed: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")


@app.get("/api/summary")
def get_summary():
    """Get the daily patrol summary."""
    if not patrol_index.frames:
        raise HTTPException(status_code=400, detail="No patrol data available yet.")
    summary = generate_daily_summary(patrol_index)
    return {"summary": summary}


@app.post("/api/load_patrol")
async def load_patrol_file(file: UploadFile = File(...)):
    """Load a previously exported patrol_results.json file into the server."""
    global patrol_index, patrol_complete
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported.")
    
    try:
        contents = await file.read()
        data = json.loads(contents)
        
        patrol_index = FrameIndex()
        patrol_index.load_from_dict(data)
        patrol_complete = True
        
        return {"message": "File loaded successfully", "stats": patrol_index.get_summary_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load JSON: {str(e)}")

@app.get("/api/patrol/stream")
async def stream_patrol():
    """Stream patrol events as server-sent events (SSE)."""
    global patrol_index, patrol_complete, patrol_running
    
    patrol_index = FrameIndex()
    patrol_complete = False
    patrol_running = True
    
    async def event_generator() -> AsyncGenerator[str, None]:
        global patrol_complete, patrol_running
        context_history = []
        telemetry_map = {t["time"]: t for t in TELEMETRY_DATA}
        default_telemetry = TELEMETRY_DATA[0]
        
        yield f"data: {json.dumps({'type': 'start', 'message': 'Patrol started', 'total_frames': len(SIMULATED_FRAMES)})}\n\n"
        
        for i, frame in enumerate(SIMULATED_FRAMES):
            telemetry = telemetry_map.get(frame["time"], default_telemetry)
            
            # Send frame-start event
            yield f"data: {json.dumps({'type': 'frame_start', 'frame_id': i+1, 'time': frame['time'], 'location': frame['location'], 'description': frame['description']})}\n\n"
            
            try:
                analysis = analyze_frame_with_ai(frame, telemetry, context_history)
            except Exception as e:
                analysis = {
                    "objects": ["unknown"],
                    "event_type": "unknown",
                    "threat_level": "low",
                    "summary": frame["description"],
                    "alert": None,
                    "log_entry": f"Frame {i+1}: {frame['description']}"
                }
            
            record = patrol_index.index_frame(
                frame_id=i+1,
                timestamp=frame["time"],
                location=frame["location"],
                raw_description=frame["description"],
                ai_analysis=analysis,
                telemetry=telemetry
            )
            
            log_entry = {
                "frame_id": i+1,
                "time": frame["time"],
                "location": frame["location"],
                "log": analysis.get("log_entry", ""),
                "threat_level": analysis.get("threat_level", "low"),
                "telemetry": telemetry
            }
            patrol_index.log_event(log_entry)
            
            threat_level = analysis.get("threat_level", "low").lower()
            has_alert = bool(analysis.get("alert"))
            
            if has_alert or threat_level in ["medium", "high", "critical"]:
                alert_msg = analysis.get("alert") or analysis.get("summary", "Potential threat detected.")
                alert = {
                    "frame_id": i+1,
                    "time": frame["time"],
                    "location": frame["location"],
                    "message": alert_msg,
                    "threat_level": threat_level if threat_level != "low" else "medium",
                    "objects": analysis.get("objects", []),
                    "telemetry": telemetry
                }
                patrol_index.add_alert(alert)
                yield f"data: {json.dumps({'type': 'alert', 'alert': alert})}\n\n"
            
            context_history.append({
                "time": frame["time"],
                "summary": analysis.get("summary", ""),
                "threat_level": analysis.get("threat_level", "low")
            })
            
            yield f"data: {json.dumps({'type': 'frame_complete', 'frame_id': i+1, 'analysis': analysis, 'telemetry': telemetry})}\n\n"
            
            await asyncio.sleep(0.5)  # Simulate real-time processing
        
        # Generate summary
        summary = generate_daily_summary(patrol_index)
        stats = patrol_index.get_summary_stats()
        
        yield f"data: {json.dumps({'type': 'complete', 'summary': summary, 'stats': stats})}\n\n"
        
        patrol_complete = True
        patrol_running = False
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)