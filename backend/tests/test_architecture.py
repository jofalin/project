import time
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.physics import ZoneFlowState, propagation_delay, time_to_capacity, weather_impact
from app.risk_engine import RiskInput, calculate_risk_matrix
from app.sop_engine import transition_state
from app.v1_schemas import AdvisoryState, OperatorAdvisory

def test_time_to_capacity():
    assert time_to_capacity(1000, 800, 80, 20) == 200 / 60
    assert time_to_capacity(1000, 800, 20, 20) is None

def test_weather_reduces_exit_velocity():
    assert weather_impact(rain_mm=3).exit_velocity_multiplier == 0.85
    assert weather_impact(rain_mm=6).exit_velocity_multiplier == 0.75

def test_propagation_gate_to_zone():
    source = ZoneFlowState("gate-a", 800, 1000, 90, 20, 30)
    target = ZoneFlowState("zone-b", 700, 1000, 30, 15, 20)
    result = propagation_delay(source, target, weather_impact(rain_mm=3))
    assert result["propagation_delay_seconds"] > 20
    assert result["effective_outflow_rate"] < 15

def test_risk_matrix_100_zones_under_15ms():
    items = [RiskInput(f"z{i}", 700, 1000, 0.08, 50 + i % 7, 35, 0.75, 0.9, 0.2) for i in range(100)]
    t0 = time.perf_counter()
    result = calculate_risk_matrix(items)
    elapsed = time.perf_counter() - t0
    assert len(result) == 100
    assert elapsed < 0.015

def test_state_machine():
    assert transition_state(AdvisoryState.PROPOSED, AdvisoryState.PENDING_APPROVAL) == AdvisoryState.PENDING_APPROVAL
    try:
        transition_state(AdvisoryState.PROPOSED, AdvisoryState.COMPLETED)
        assert False
    except ValueError:
        pass

def test_advisory_schema_is_strict():
    item = OperatorAdvisory(
        incident_id=uuid4(),
        severity="HIGH",
        target_zone_ids=["zone-a"],
        recommended_sop_id="SOP-1",
        action_items=["Observe"],
        confidence_score=0.9,
    )
    assert item.model_dump()["severity"] == "HIGH"

def test_v1_propagation_route():
    with TestClient(app) as client:
        payload = {
            "zones": [
                {"zone_id":"gate-a","occupancy":800,"max_capacity":1000,"inflow_rate":90,"outflow_rate":20,"base_travel_seconds":30},
                {"zone_id":"zone-b","occupancy":700,"max_capacity":1000,"inflow_rate":30,"outflow_rate":15,"base_travel_seconds":20}
            ],
            "edges":[{"source_zone_id":"gate-a","target_zone_id":"zone-b"}],
            "weather":{"rain_mm":3}
        }
        response = client.post("/api/v1/predict/propagation", json=payload)
        assert response.status_code == 200
        assert response.json()["segments"][0]["weather_exit_velocity_multiplier"] == 0.85
