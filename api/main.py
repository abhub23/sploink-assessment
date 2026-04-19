from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .models import EventInput, EventResponse, SessionSummary, DetectionResult
from . import storage
from . import detection

app = FastAPI(title="Agent Monitoring API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/events", response_model=EventResponse)
async def ingest_event(event: EventInput):
    return storage.add_event(event)


@app.post("/events/batch", response_model=List[EventResponse])
async def ingest_events_batch(events: List[EventInput]):
    results = []
    for event in events:
        results.append(storage.add_event(event))
    return results


@app.get("/events/{session_id}", response_model=List[EventResponse])
async def get_session_events(session_id: str):
    return storage.get_session_events(session_id)


@app.get("/sessions", response_model=List[SessionSummary])
async def list_sessions():
    return storage.get_all_sessions()


@app.get("/sessions/{session_id}", response_model=SessionSummary)
async def get_session(session_id: str):
    session = storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions/{session_id}/analyze", response_model=DetectionResult)
async def analyze_session(session_id: str):
    events = storage.get_session_events(session_id)
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")

    event_dicts = [e.model_dump() for e in events]
    return detection.analyze_session(event_dicts)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.delete("/clear")
async def clear_storage():
    storage.clear()
    return {"status": "cleared"}
