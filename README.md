# AI Powered Crowd Intelligence and Decision Support System

Integrated React + FastAPI + SQLite command center for whole-venue crowd monitoring and predictive crowd intelligence.

## Combined implementation
- SQLite-backed whole-venue dashboard with live KPIs, alerts, events and zone activity
- Interactive SVG risk map with click, zoom and pan
- Daily/weekly/monthly reports with CSV export and print
- INFO/WARNING/ERROR logging to database and local log file
- Mock data controls for slow/normal/fast simulation
- Predictive Crowd Flow with adjacency, probability, confidence and ETA
- Weather + event schedule context
- Dynamic SOP generator with human-review gate
- What-If crowd simulation
- Multi-modal Police/Citizen/Volunteer reports
- Incident timeline
- Operator AI chat
- Advisory approve/reject workflow
- New React "Predictive Intelligence" page connected to the same FastAPI backend

## Run

Backend:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:
```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173
API: http://localhost:8000

The project is still a demo: predictive flow uses deterministic demo context, weather is demo-fallback, and operator advisories always require human review before physical-world action.
