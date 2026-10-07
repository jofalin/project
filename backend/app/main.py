from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services import build_context, predict_flow, get_weather, get_schedule, answer_operator, generate_advisories, approve_advisory, reject_advisory

app = FastAPI(title="Crowd Safety Intelligence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "branch_scope": "one"}

@app.get("/api/predictive-flow")
def predictive_flow():
    return {"predictions": predict_flow(build_context())}

@app.get("/api/weather")
def weather():
    return get_weather()

@app.get("/api/schedule")
def schedule():
    return get_schedule()

@app.get("/api/context")
def context():
    return build_context()

@app.post("/api/operator-chat")
def operator_chat(payload: dict):
    return answer_operator(str(payload.get("message", "")), build_context(), payload.get("history", []))

@app.get("/api/advisories")
def advisories():
    return {"advisories": generate_advisories(build_context())}

@app.post("/api/advisories/{advisory_id}/approve")
def approve(advisory_id: str):
    return approve_advisory(advisory_id)

@app.post("/api/advisories/{advisory_id}/reject")
def reject(advisory_id: str):
    return reject_advisory(advisory_id)
