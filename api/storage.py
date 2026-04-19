import uuid
from datetime import datetime
from typing import Dict, List, Optional
from .models import EventInput, EventResponse, SessionSummary
from . import detection


class Storage:
    def __init__(self):
        self._events: Dict[str, List[EventResponse]] = {}
        self._sessions: Dict[str, SessionSummary] = {}

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _get_dedup_key(self, event: EventInput) -> str:
        return f"{event.session_id}:{event.step}:{event.action}:{event.input[:50]}"

    def add_event(self, event: EventInput) -> EventResponse:
        dedup_key = self._get_dedup_key(event)

        if event.session_id not in self._events:
            self._events[event.session_id] = []

        for existing in self._events[event.session_id]:
            if (
                existing.step == event.step
                and existing.action == event.action
                and existing.input == event.input
            ):
                return existing

        event_id = self._generate_id()

        metadata_dict = {}
        if event.metadata:
            metadata_dict = event.metadata.model_dump(exclude_none=True)

        response = EventResponse(
            id=event_id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            step=event.step,
            action=event.action,
            input=event.input,
            output=event.output,
            metadata=metadata_dict,
        )

        self._events[event.session_id].append(response)
        self._events[event.session_id].sort(key=lambda x: (x.step, x.timestamp))

        self._update_session(event.session_id)

        return response

    def _update_session(self, session_id: str):
        events = self._events.get(session_id, [])

        if not events:
            return

        total_steps = len(events)
        success_count = 0
        failure_count = 0
        action_dist: Dict[str, int] = {}

        for event in events:
            status = (
                event.metadata.get("status", "unknown") if event.metadata else "unknown"
            )
            if status == "success":
                success_count += 1
            elif status == "failure":
                failure_count += 1

            action_dist[event.action] = action_dist.get(event.action, 0) + 1

        event_dicts = [e.model_dump() for e in events]
        analysis = detection.analyze_session(event_dicts)

        self._sessions[session_id] = SessionSummary(
            session_id=session_id,
            status=analysis["status"],
            total_steps=total_steps,
            success_count=success_count,
            failure_count=failure_count,
            action_distribution=action_dist,
            detected_issues=analysis["issues"],
            last_updated=datetime.utcnow(),
        )

    def get_event(self, session_id: str, event_id: str) -> Optional[EventResponse]:
        events = self._events.get(session_id, [])
        for event in events:
            if event.id == event_id:
                return event
        return None

    def get_session_events(self, session_id: str) -> List[EventResponse]:
        return sorted(
            self._events.get(session_id, []), key=lambda x: (x.step, x.timestamp)
        )

    def get_all_sessions(self) -> List[SessionSummary]:
        return list(self._sessions.values())

    def get_session(self, session_id: str) -> Optional[SessionSummary]:
        return self._sessions.get(session_id)

    def clear(self):
        self._events.clear()
        self._sessions.clear()


storage = Storage()
