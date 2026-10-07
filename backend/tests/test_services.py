from app.services import (
    build_context, predict_flow, get_weather, generate_advisories,
    generate_sop, get_risk_history, get_reports, simulate_scenario
)

def test_predictive_flow_has_adjacency_probability_and_eta():
    predictions = predict_flow(build_context())
    assert predictions
    first = predictions[0]
    assert first["source_zone"] == "Gate A"
    assert first["target_zone"] == "Zone B"
    assert 0 <= first["probability"] <= 1
    assert first["eta_seconds"] > 0

def test_weather_is_context_only():
    weather = get_weather()
    assert weather["risk_modifier"] > 0
    assert weather["source"] == "demo-fallback"

def test_advisory_requires_human_review():
    advisories = generate_advisories(build_context())
    assert advisories
    assert all(item["human_review_required"] is True for item in advisories)

def test_sop_is_draft_and_explainable():
    sop = generate_sop(build_context())
    assert sop["status"] == "DRAFT"
    assert sop["human_review_required"] is True
    assert sop["observation"]
    assert sop["trend"]
    assert sop["prediction"]
    assert sop["recommendations"]

def test_history_and_reports_exist():
    assert len(get_risk_history()) >= 3
    assert len(get_reports()) >= 1

def test_simulation_changes_prediction_context():
    result = simulate_scenario({
        "label": "stress test",
        "weather_modifier": 0.3,
        "zones": {"Gate A": {"density": 98, "trend": 20, "direction": "Zone B"}}
    })
    assert result["predictions"]
    assert result["highest_risk_zone"] == "Gate A"
    assert result["summary"]
