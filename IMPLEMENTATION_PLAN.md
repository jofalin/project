# AI Powered Crowd Intelligence and Decision Support System

## Folder Structure

frontend/
  src/pages/Dashboard.jsx
  src/pages/RiskMap.jsx
  src/pages/Reports.jsx
  src/pages/SystemLogs.jsx
  src/pages/MockDataControl.jsx
  src/components/RiskMapSVG.jsx
backend/
  app.py
  database.py
  models.py
  reports.py
  logging_service.py
  mock_generator.py
  routes/
    zones.py
    alerts.py
    reports.py
    logs.py
    mock.py

## Database Tables
zones, events, alerts, system_logs

## APIs
GET /zones
GET /zones/{id}
GET /alerts
GET /events
GET /reports/daily
GET /reports/weekly
GET /reports/monthly
GET /logs
POST /mock/start
POST /mock/stop
POST /mock/reset
