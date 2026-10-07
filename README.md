# AI Powered Crowd Intelligence and Decision Support System

React + FastAPI + SQLite command center for whole-venue crowd monitoring.

## Implemented on fexo
- Dashboard with live KPIs, trend, risk distribution, alerts and zone activity
- Interactive SVG Risk Map with hover/click, zoom and pan
- Daily/weekly/monthly reports with CSV export and print
- SQLite database for zones, events, alerts and system logs
- INFO/WARNING/ERROR logging to database and local log file
- Mock data controls for slow/normal/fast simulation

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
