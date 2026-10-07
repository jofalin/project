Crowd Safety Intelligence
=========================

Branch one implements Predictive Crowd Flow, Weather + Event Schedule Context, Operator AI Chat, and Advisory / Recommendation Generator.

Run backend:

    cd backend
    python -m venv .venv
    .venv\\Scripts\\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Then open frontend/index.html. It connects to http://localhost:8000/api when opened directly.

Architecture: Crowd Context -> Predictive Flow -> AI Context -> Advisory -> Human Review.

External weather and LLM integrations are fallback-safe. Recommendations never directly control gates, deploy responders, broadcast messages, or perform physical-world actions.
