# Agent Monitoring System

A monitoring system for AI agents that ingests activity events, detects behavioral issues (loops, drift, failures), and surfaces insights via a web UI.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐
│ Agent       │     │ FastAPI     │     │ Detection   │     │ Next.js  │
│ Simulator   │────▶│ API         │────▶│ Engine      │────▶│ Frontend │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────┘
     (port 8000)                              (port 3000)
```

## Quick Start

### 1. Install Dependencies

```bash
# API backend
pip install -r requirements.txt

# Frontend
cd web && npm install
```

### 2. Start the Backend (port 8000)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 3. Start the Frontend (port 3000)

```bash
cd web && npm run dev
```

### 4. Run Agent Simulator

```bash
# Normal behavior
python agent/simulator.py --scenario normal

# Looping behavior
python agent/simulator.py --scenario loop

# Drift behavior  
python agent/simulator.py --scenario drift

# Failure behavior
python agent/simulator.py --scenario failure
```

### 5. Open Dashboard

Visit http://localhost:3000 to view the sessions dashboard.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /events | Ingest a single event |
| POST | /events/batch | Ingest multiple events |
| GET | /events/{session_id} | Get session events |
| GET | /sessions | List all sessions |
| GET | /sessions/{session_id} | Get session summary |
| GET | /sessions/{session_id}/analyze | Get detection results |

## Event Schema

```json
{
  "session_id": "session_abc123",
  "timestamp": 1699999999,
  "step": 1,
  "action": "read_file",
  "input": "src/main.py",
  "output": "File contents...",
  "metadata": {
    "file": "src/main.py",
    "status": "success"
  }
}
```

Valid actions: `read_file`, `write_file`, `run_command`, `llm_call`
Valid statuses: `success`, `failure`, `unknown`

## Detection Logic

### Loop Detection
- Uses n-gram similarity (n=2) on action sequences
- Compares sliding windows of 5 actions
- Detects patterns with ≥70% similarity
- Not just identical strings - uses edit distance and semantic variation

### Drift Detection
- Splits session into first/second halves
- Detects action set changes between halves
- Uses string similarity on inputs to detect intent shifts
- Threshold: <50% similarity indicates drift

### Failure Detection
- **Consecutive failures**: ≥3 in a row = high severity
- **Failure rate**: >30% of events = high severity

### Status Priority
1. `failing` (high severity issues)
2. `looping` (loop detected)
3. `drifting` (drift detected)
4. `healthy` (no issues)

## Trade-offs

### In-Memory Storage
- **Pro**: Simple, fast, no setup needed
- **Con**: Data lost on restart, limited scalability
- **Decision**: Chose for simplicity given time constraints

### Real-Time Processing
- **Pro**: Immediate detection results
- **Con**: More computation per request
- **Decision**: Simple enough to process inline

### Simple Thresholds
- **Pro**: Easy to understand and tune
- **Con**: May not capture all edge cases
- **Decision**: Start simple, can be improved later

### Single Worker
- **Pro**: No concurrency issues
- **Con**: Can't handle high throughput
- **Decision**: Sufficient for demo/local use

## Edge Cases Handled

| Edge Case | Solution |
|----------|----------|
| Duplicate events | Dedupe key: session_id + step + action + input[:50] |
| Out-of-order | Sort by (step, timestamp) on retrieve |
| Missing metadata | Default to status: "unknown" |
| Late events | Re-process session on arrival |
| Duplicate step numbers | Composite sort: (step, timestamp) |
| Fast bursts | Async handling (no blocking) |
| Mixed sessions | Session isolation in storage |

## Project Structure

```
├── api/
│   ├── main.py          # FastAPI app
│   ├── models.py       # Pydantic models
│   ├── storage.py      # In-memory storage
│   └── detection.py    # Detection logic
├── agent/
│   └── simulator.py    # Agent CLI
├── web/               # Next.js frontend
│   ├── app/
│   │   ├── page.tsx
│   │   ├── sessions/
│   │   └── sessions/[sessionId]/
│   ├── package.json
│   └── tsconfig.json
├── requirements.txt
└── README.md
```