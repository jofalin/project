from app.services import build_context, predict_flow, generate_advisories, answer_operator

def test_predictive_flow_has_adjacent_prediction():
    predictions = predict_flow(build_context())
    assert predictions
    assert predictions[0]["source_zone"] == "Gate A"
    assert predictions[0]["target_zone"] == "Zone B"
    assert 0 <= predictions[0]["probability"] <= 1
    assert predictions[0]["eta_seconds"] > 0

def test_weather_is_context_only():
    context = build_context()
    assert context["weather"]["risk_modifier"] > 0
    assert context["zones"]["Exit C"]["risk"] == "Safe"

def test_advisory_requires_human_review():
    advisories = generate_advisories(build_context())
    assert advisories
    assert all(a["human_review_required"] for a in advisories)

def test_chat_uses_predictive_context():
    response = answer_operator("Where will congestion move next?", build_context(), [])
    assert response["source"] == "predictive-flow"
