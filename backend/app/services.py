from datetime import datetime, timezone, timedelta
from math import ceil
from uuid import uuid4

ZONES = {
    "Gate A": {"neighbors": ["Zone B"], "density": 82, "trend": 12, "direction": "Zone B", "risk": "Warning"},
    "Zone B": {"neighbors": ["Central Area"], "density": 58, "trend": 7, "direction": "Central Area", "risk": "Watch"},
    "Central Area": {"neighbors": ["Exit C"], "density": 41, "trend": 2, "direction": "Exit C", "risk": "Watch"},
    "Exit C": {"neighbors": [], "density": 18, "trend": -1, "direction": None, "risk": "Safe"},
}

EVENTS = [
    {"event": "Main Performance", "start_time": "2026-10-07T20:00:00+05:30", "end_time": "2026-10-07T21:00:00+05:30", "affected_zones": ["Central Area", "Gate A"], "expected_surge": "high"},
    {"event": "Closing Ceremony", "start_time": "2026-10-07T21:45:00+05:30", "end_time": "2026-10-07T22:15:00+05:30", "affected_zones": ["Central Area", "Exit C"], "expected_surge": "medium"},
]
STATE = {}

def get_weather():
    return {
        "condition": "Light Rain",
        "temperature_c": 27,
        "rain_mm": 2.4,
        "visibility_km": 7.5,
        "wind_kph": 14,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "demo-fallback",
        "risk_modifier": 0.12,
        "context": "Rain increases slip and crowd-management context risk.",
    }

def get_schedule():
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    enriched = []
    for event in EVENTS:
        start = datetime.fromisoformat(event["start_time"])
        item = dict(event)
        delta = (start - now).total_seconds()
        item["minutes_until"] = max(0, round(delta / 60))
        item["active"] = start <= now <= datetime.fromisoformat(event["end_time"])
        enriched.append(item)
    active = next((e for e in enriched if e["active"]), None)
    upcoming = next((e for e in enriched if e["minutes_until"] > 0), None)
    return {"current_event": active, "next_event": upcoming, "events": enriched}

def build_context():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zones": ZONES,
        "weather": get_weather(),
        "schedule": get_schedule(),
        "alerts": [{"zone": "Gate A", "state": "Warning", "message": "Density is increasing."}],
        "reports": [],
    }

def _severity(probability):
    if probability >= .85: return "CRITICAL"
    if probability >= .65: return "HIGH"
    if probability >= .40: return "MEDIUM"
    return "LOW"

def predict_flow(context):
    predictions = []
    weather_bonus = context["weather"]["risk_modifier"]
    for source, data in context["zones"].items():
        for target in data["neighbors"]:
            density_factor = min(data["density"] / 100, 1)
            trend_factor = min(max(data["trend"], 0) / 20, 1)
            direction_factor = 1 if data["direction"] == target else .25
            risk_factor = {"Safe": 0, "Watch": .2, "Warning": .45, "Critical": .7}.get(data["risk"], 0)
            probability = min(.98, .12 + .30*density_factor + .25*trend_factor + .18*direction_factor + .12*risk_factor + .05*weather_bonus)
            eta = max(30, ceil(150 - data["density"] - max(data["trend"], 0)*4))
            confidence = min(.95, .55 + trend_factor*.25 + direction_factor*.12)
            predictions.append({
                "id": f"{source}-{target}".replace(" ", "-").lower(),
                "source_zone": source,
                "target_zone": target,
                "probability": round(probability, 2),
                "eta_seconds": eta,
                "confidence": round(confidence, 2),
                "severity": _severity(probability),
                "reason": f"{data['density']}% density, trend +{data['trend']}%, movement toward {target}.",
            })
    return predictions

def answer_operator(message, context, history):
    q = message.lower()
    predictions = predict_flow(context)
    highest = max(context["zones"].items(), key=lambda x: x[1]["density"])
    if any(k in q for k in ["highest", "risk", "danger"]):
        z, d = highest
        return {"answer": f"{z} currently has the highest density at {d['density']}% and is in {d['risk']}. Its trend is +{d['trend']}%.", "source": "live-context"}
    if any(k in q for k in ["move", "next", "congestion"]):
        p = max(predictions, key=lambda x: x["probability"]) if predictions else None
        if p:
            return {"answer": f"Congestion is most likely to propagate from {p['source_zone']} to {p['target_zone']} in about {p['eta_seconds']} seconds ({p['probability']*100:.0f}% probability). {p['reason']}", "source": "predictive-flow"}
    if "weather" in q or "rain" in q:
        w = context["weather"]
        return {"answer": f"Current weather is {w['condition']} at {w['temperature_c']}°C with {w['rain_mm']} mm rain. Context risk modifier is +{w['risk_modifier']:.2f}.", "source": "weather"}
    if "event" in q or "schedule" in q:
        e = context["schedule"]["current_event"] or context["schedule"]["next_event"]
        if e:
            timing = "active now" if e.get("active") else f"in {e['minutes_until']} minutes"
            return {"answer": f"{e['event']} is {timing}, affects {', '.join(e['affected_zones'])}, and has {e['expected_surge']} expected surge.", "source": "schedule"}
    if any(k in q for k in ["recommend", "action", "advice"]):
        ads = generate_advisories(context)
        return {"answer": ads[0]["recommendation"] if ads else "No advisory is currently generated from available data.", "source": "advisory-engine"}
    return {"answer": "I can answer about current risk, density trends, predicted crowd movement, weather, event schedule, and recommended actions using available project context.", "source": "deterministic-fallback"}

def generate_advisories(context):
    results = []
    for p in predict_flow(context):
        if p["severity"] in {"HIGH", "CRITICAL"}:
            results.append({
                "id": str(uuid4())[:8],
                "category": "CROWD_FLOW",
                "status": "DRAFT",
                "observation": f"{p['source_zone']} has conditions that can propagate crowd pressure.",
                "trend": p["reason"],
                "prediction": f"{p['target_zone']} has {p['probability']*100:.0f}% predicted congestion probability in about {p['eta_seconds']} seconds.",
                "recommendation": f"Consider positioning trained volunteers near {p['target_zone']} and guiding incoming visitors toward an alternate route if available.",
                "expected_benefit": "Reduce pressure on the predicted target zone and distribute crowd flow.",
                "human_review_required": True,
            })
    if context["weather"]["risk_modifier"] > .1:
        results.append({
            "id": str(uuid4())[:8],
            "category": "WEATHER",
            "status": "DRAFT",
            "observation": context["weather"]["context"],
            "trend": "Weather conditions can increase movement caution.",
            "prediction": "Crowd movement may become slower or less evenly distributed.",
            "recommendation": "Consider increasing monitoring around high-density transition areas and communicating safe movement guidance.",
            "expected_benefit": "Reduce weather-related crowd disruption.",
            "human_review_required": True,
        })
    return results

def approve_advisory(advisory_id):
    STATE[advisory_id] = "APPROVED"
    return {"id": advisory_id, "status": "APPROVED", "message": "Approved by operator. No automatic physical-world action was taken."}

def reject_advisory(advisory_id):
    STATE[advisory_id] = "REJECTED"
    return {"id": advisory_id, "status": "REJECTED"}
