# Notes: HEALER traces read-only integration

Planned minimal contract:
- Endpoint: GET /api/v1/healer/bridge/traces
- Query: session_id (optional), phase (optional), severity (optional), limit (optional)
- Response: { status: "ok", traces: [...] }

Backend data source:
- backend/core/trace_collector.py (TraceCollector.list_traces)

Front-end:
- Reuse existing style from xray TraceHistory (if needed) or implement a small card.

Important:
- HEALER bridge currently subscribes to PAD+ TraceCollector events, but TraceCollector in this repo is in-memory.
- So traces endpoint should be best-effort and session-scoped when possible.

