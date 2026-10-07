from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .physics import ZoneFlowState, propagate_network, weather_impact
from .risk_engine import RiskInput, RiskWeights, calculate_risk_matrix
from .v1_schemas import (
    PropagationRequest, PropagationResponse, PropagationSegment,
    RiskMatrixRequest, RiskMatrixResponse, RiskZoneResult,
    OperatorAdvisory, AdvisoryCreateRequest, AdvisoryTransitionRequest,
    TelemetrySnapshotIn, SOPContextRequest, AgentGenerateRequest, AdvisoryState
)
from .production_db import get_session
from .production_models import Advisory, AdvisoryState as DBAdvisoryState, AuditLog, TelemetrySnapshot
from .sop_engine import build_context_wrapper, transition_state, AdvisoryOrchestrator
from .rag import PostgresSOPRetriever
from .config import get_settings
from .llm_client import OpenAICompatibleAdvisoryClient
from .runtime import websocket_manager

router = APIRouter()

@router.post("/predict/propagation", response_model=PropagationResponse)
async def predict_propagation(payload: PropagationRequest):
    states = [
        ZoneFlowState(
            zone_id=z.zone_id,
            occupancy=z.occupancy,
            max_capacity=z.max_capacity,
            inflow_rate=z.inflow_rate,
            outflow_rate=z.outflow_rate,
            base_travel_seconds=z.base_travel_seconds,
            warning_threshold=z.warning_threshold,
        )
        for z in payload.zones
    ]
    by_id = {s.zone_id for s in states}
    edges = [(e.source_zone_id, e.target_zone_id) for e in payload.edges]
    unknown = {node for edge in edges for node in edge if node not in by_id}
    if unknown:
        raise HTTPException(422, f"Unknown zone ids: {sorted(unknown)}")
    segments = propagate_network(states, edges, weather_impact(payload.weather.rain_mm, payload.weather.severity))
    return PropagationResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        segments=[PropagationSegment(**segment) for segment in segments],
    )

@router.post("/analytics/risk-matrix", response_model=RiskMatrixResponse)
async def risk_matrix(payload: RiskMatrixRequest):
    try:
        weights = RiskWeights(**payload.weights) if payload.weights else RiskWeights()
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, f"Invalid risk weights: {exc}") from exc
    weather = payload.weather.severity if payload.weather.severity else min(payload.weather.rain_mm / 10.0, 1.0)
    items = [
        RiskInput(
            zone_id=z.zone_id,
            occupancy=z.occupancy,
            max_capacity=z.max_capacity,
            density_change_per_minute=z.density_change_per_minute,
            inflow_rate=z.inflow_rate,
            outflow_rate=z.outflow_rate,
            warning_threshold=z.warning_threshold,
            critical_threshold=z.critical_threshold,
            weather_severity=weather,
        )
        for z in payload.zones
    ]
    results = calculate_risk_matrix(items, weights)
    return RiskMatrixResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        results=[
            RiskZoneResult(
                zone_id=r.zone_id,
                score=r.score,
                hazard_state=r.hazard_state.value,
                early_warning=r.early_warning,
                density_ratio=r.density_ratio,
                normalized_density_rate=r.normalized_density_rate,
                bottleneck_factor=r.bottleneck_factor,
                weather_severity=r.weather_severity,
            )
            for r in results
        ],
    )


@router.post("/agent/generate", response_model=OperatorAdvisory)
async def generate_agent_advisory(payload: AgentGenerateRequest, session: AsyncSession = Depends(get_session)):
    stmt = (select(TelemetrySnapshot).where(TelemetrySnapshot.zone_id.in_(payload.zone_ids)).order_by(TelemetrySnapshot.captured_at.desc()).limit(100))
    telemetry = [dict(row) for row in (await session.execute(stmt)).mappings().all()]
    context = await build_context_wrapper(telemetry=telemetry, weather=payload.weather, gate_throughput=payload.gate_throughput, query_embedding=payload.query_embedding, retriever=PostgresSOPRetriever(session))
    settings = get_settings()
    client = OpenAICompatibleAdvisoryClient() if settings.llm_base_url and settings.llm_api_key else None
    try:
        advisory, trace = await AdvisoryOrchestrator(client).generate(context)
    except Exception as exc:
        advisory, trace = await AdvisoryOrchestrator(None).generate(context)
        trace = {**trace, "llm_fallback": True, "error_type": type(exc).__name__}
    session.add(Advisory(incident_id=advisory.incident_id, state=DBAdvisoryState.PROPOSED, severity=advisory.severity.value, target_zone_ids=advisory.target_zone_ids, recommended_sop_id=advisory.recommended_sop_id, action_items=advisory.action_items, confidence_score=advisory.confidence_score))
    session.add(AuditLog(incident_id=advisory.incident_id, operator_id="agent", action_taken="GENERATE_ADVISORY", ambient_telemetry={"telemetry": telemetry, "weather": payload.weather, "gate_throughput": payload.gate_throughput}, llm_reasoning_trace=trace))
    await session.commit()
    return advisory

@router.post("/agent/advisories", response_model=OperatorAdvisory)
async def create_advisory(payload: AdvisoryCreateRequest, session: AsyncSession = Depends(get_session)):
    advisory = Advisory(
        incident_id=payload.advisory.incident_id,
        state=DBAdvisoryState.PROPOSED,
        severity=payload.advisory.severity.value,
        target_zone_ids=payload.advisory.target_zone_ids,
        recommended_sop_id=payload.advisory.recommended_sop_id,
        action_items=payload.advisory.action_items,
        confidence_score=payload.advisory.confidence_score,
        operator_id=payload.operator_id,
    )
    session.add(advisory)
    session.add(AuditLog(
        incident_id=payload.advisory.incident_id,
        operator_id=payload.operator_id,
        action_taken="CREATE_ADVISORY",
        ambient_telemetry=payload.ambient_telemetry,
        llm_reasoning_trace=payload.llm_trace,
    ))
    await session.commit()
    return payload.advisory

@router.post("/agent/advisories/{incident_id}/transition", response_model=OperatorAdvisory)
async def transition_advisory(
    incident_id: str,
    payload: AdvisoryTransitionRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        incident_uuid = UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(422, "incident_id must be a UUID") from exc
    advisory = await session.get(Advisory, incident_uuid)
    if not advisory:
        raise HTTPException(404, "Advisory not found")
    current = AdvisoryState(advisory.state.value)
    try:
        new_state = transition_state(current, payload.target_state)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    advisory.state = DBAdvisoryState(new_state.value)
    advisory.operator_id = payload.operator_id
    session.add(AuditLog(
        incident_id=incident_uuid,
        operator_id=payload.operator_id,
        action_taken=f"STATE:{payload.target_state.value}",
        ambient_telemetry=payload.ambient_telemetry,
        llm_reasoning_trace=payload.llm_trace,
    ))
    await session.commit()
    return OperatorAdvisory(
        incident_id=advisory.incident_id,
        severity=advisory.severity,
        target_zone_ids=advisory.target_zone_ids,
        recommended_sop_id=advisory.recommended_sop_id,
        action_items=advisory.action_items,
        confidence_score=advisory.confidence_score,
    )

@router.post("/telemetry/snapshot")
async def ingest_snapshot(payload: TelemetrySnapshotIn, session: AsyncSession = Depends(get_session)):
    captured_at = datetime.now(timezone.utc)
    snapshot = TelemetrySnapshot(
        captured_at=captured_at,
        zone_id=payload.zone_id,
        occupancy=payload.occupancy,
        inflow_rate=payload.inflow_rate,
        outflow_rate=payload.outflow_rate,
        density_ratio=payload.density_ratio,
        weather_severity=payload.weather_severity,
        source=payload.source,
    )
    session.add(snapshot)
    await session.commit()
    data = payload.model_dump()
    data["captured_at"] = captured_at.isoformat()
    await websocket_manager.publish({"type": "telemetry", "data": data})
    return {"accepted": True, "captured_at": captured_at.isoformat()}

@router.post("/agent/context")
async def build_agent_context(payload: SOPContextRequest, session: AsyncSession = Depends(get_session)):
    stmt = (
        select(TelemetrySnapshot)
        .where(TelemetrySnapshot.zone_id.in_(payload.zone_ids))
        .order_by(TelemetrySnapshot.captured_at.desc())
        .limit(100)
    )
    telemetry = [dict(row) for row in (await session.execute(stmt)).mappings().all()]
    context = await build_context_wrapper(
        telemetry=telemetry,
        weather=payload.weather,
        gate_throughput=payload.gate_throughput,
        query_embedding=payload.query_embedding,
        retriever=PostgresSOPRetriever(session),
    )
    return {
        "generated_at": context.generated_at,
        "telemetry": context.telemetry,
        "weather": context.weather,
        "gate_throughput": context.gate_throughput,
        "sop_documents": context.sop_documents,
    }

@router.websocket("/ws/telemetry")
async def telemetry_socket(websocket: WebSocket):
    await websocket_manager.handle(websocket)
