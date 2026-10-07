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


def get_risk_history():
    return [
        {"time": "20:00", "gate_a": 46, "zone_b": 28, "central": 22, "exit_c": 12},
        {"time": "20:05", "gate_a": 55, "zone_b": 34, "central": 25, "exit_c": 13},
        {"time": "20:10", "gate_a": 64, "zone_b": 42, "central": 31, "exit_c": 15},
        {"time": "20:15", "gate_a": 73, "zone_b": 49, "central": 36, "exit_c": 17},
        {"time": "20:20", "gate_a": 82, "zone_b": 58, "central": 41, "exit_c": 18},
    ]

def get_reports():
    return [
        {"id": "R-101", "type": "POLICE", "message": "Crowd gathering near Gate A.", "age_seconds": 120},
        {"id": "R-102", "type": "CITIZEN", "message": "Passage near Zone B is partially blocked.", "age_seconds": 75},
        {"id": "R-103", "type": "VOLUNTEER", "message": "High density observed near Central Area.", "age_seconds": 35},
    ]

def get_incidents(context=None):
    context = context or build_context()
    incidents = []
    for p in predict_flow(context):
        if p["severity"] in {"HIGH", "CRITICAL"}:
            incidents.append({
                "time": context["timestamp"],
                "severity": p["severity"],
                "title": f"{p['source_zone']} → {p['target_zone']}",
                "message": f"{p['probability']*100:.0f}% congestion probability in {p['eta_seconds']} seconds.",
            })
    if context["weather"]["risk_modifier"] > .1:
        incidents.append({
            "time": context["timestamp"],
            "severity": "WATCH",
            "title": "Weather context",
            "message": "Rain may slow movement and increase slip/crowd-management risk.",
        })
    return incidents

def simulate_scenario(overrides):
    context = build_context()
    zones = {name: dict(data) for name, data in context["zones"].items()}
    for name, changes in (overrides.get("zones") or {}).items():
        if name in zones:
            if "density" in changes:
                zones[name]["density"] = max(0, min(100, float(changes["density"])))
            if "trend" in changes:
                zones[name]["trend"] = float(changes["trend"])
            if "direction" in changes:
                zones[name]["direction"] = changes["direction"]
    context["zones"] = zones
    if "weather_modifier" in overrides:
        context["weather"]["risk_modifier"] = max(0, min(1, float(overrides["weather_modifier"])))
    predictions = predict_flow(context)
    return {
        "inputs": overrides,
        "predictions": predictions,
        "highest_risk_zone": max(zones.items(), key=lambda x: x[1]["density"])[0],
        "summary": "Scenario indicates elevated downstream pressure." if any(p["severity"] in {"HIGH","CRITICAL"} for p in predictions) else "Scenario remains within lower predicted flow pressure.",
    }

def generate_sop(context=None):
    context = context or build_context()
    predictions = predict_flow(context)
    high = [p for p in predictions if p["severity"] in {"HIGH", "CRITICAL"}]
    target = high[0] if high else (predictions[0] if predictions else None)
    if target:
        observation = f"{target['source_zone']} is creating downstream pressure toward {target['target_zone']}."
        trend = target["reason"]
        prediction = f"{target['target_zone']} has {target['probability']*100:.0f}% predicted congestion probability in about {target['eta_seconds']} seconds."
        recommendation = [
            f"Position trained volunteers near {target['target_zone']}.",
            f"Monitor the route from {target['source_zone']} to {target['target_zone']}.",
            "Prepare an alternate routing/public guidance message if pressure continues."
        ]
    else:
        observation = "No high-risk propagation is currently detected."
        trend = "Current zone trends remain comparatively stable."
        prediction = "No immediate downstream congestion escalation is predicted."
        recommendation = ["Continue routine monitoring and keep the operator dashboard active."]
    return {
        "status": "DRAFT",
        "human_review_required": True,
        "observation": observation,
        "trend": trend,
        "prediction": prediction,
        "recommendations": recommendation,
        "expected_benefit": "Reduce crowd concentration and improve response readiness before congestion escalates.",
        "approval_note": "Operator must review, edit if needed, and approve before any real-world action."
    }
