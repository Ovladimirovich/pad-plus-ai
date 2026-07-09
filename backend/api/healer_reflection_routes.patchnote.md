# Notes: HEALER reflection integration follow-up

## What exists today
- `GET /api/v1/healer/bridge/status`
- `GET /api/v1/healer/bridge/mode`
- `POST /api/v1/healer/bridge/mode`
- `POST /api/v1/healer/bridge/diagnose`
- `POST /api/v1/healer/bridge/cycle`
- `GET /api/v1/healer/bridge/reports/latest?min_severity=...`
- `GET/POST/PUT/DELETE /api/v1/healer/bridge/auto-cycle`

## Missing for current plan
- No endpoint like `GET /api/v1/healer/bridge/reflection/latest`
- No endpoint like `GET /api/v1/healer/bridge/traces?...`
- No endpoint like `POST /api/v1/healer/bridge/reports/fix`

So the next implementation step must be:
1) Add a reflection endpoint to `backend/api/healer_routes.py`, or reuse an existing data source from HEALER Orchestrator/meta.
2) Wire `frontend/src/pages/HealerPage.jsx` to fetch it and pass into `HealerReflection`.

