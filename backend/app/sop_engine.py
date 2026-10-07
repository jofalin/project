from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4
from .v1_schemas import AdvisoryState, OperatorAdvisory

ALLOWED_TRANSITIONS = {
    AdvisoryState.PROPOSED: {AdvisoryState.PENDING_APPROVAL, AdvisoryState.OVERRIDDEN},
    AdvisoryState.PENDING_APPROVAL: {AdvisoryState.APPROVED, AdvisoryState.OVERRIDDEN},
    AdvisoryState.APPROVED: {AdvisoryState.IN_EXECUTION, AdvisoryState.OVERRIDDEN},
    AdvisoryState.IN_EXECUTION: {AdvisoryState.COMPLETED, AdvisoryState.OVERRIDDEN},
    AdvisoryState.COMPLETED: set(),
    AdvisoryState.OVERRIDDEN: set(),
}

class SOPRetriever(Protocol):
    async def search(self, embedding: list[float], limit: int = 5) -> list[dict]: ...

@dataclass(frozen=True, slots=True)
class VenueContext:
    generated_at: str
    telemetry: list[dict]
    weather: dict
    gate_throughput: dict
    sop_documents: list[dict]

async def build_context_wrapper(telemetry, weather, gate_throughput, query_embedding, retriever) -> VenueContext:
    docs = await retriever.search(query_embedding, limit=5) if retriever and query_embedding else []
    return VenueContext(datetime.now(timezone.utc).isoformat(), telemetry, weather, gate_throughput, docs)

def transition_state(current: AdvisoryState, target: AdvisoryState) -> AdvisoryState:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid advisory transition: {current.value} -> {target.value}")
    return target

class AdvisoryOrchestrator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def generate(self, context: VenueContext) -> tuple[OperatorAdvisory, dict]:
        if self.llm_client:
            raw, trace = await self.llm_client.generate_advisory(context)
            return OperatorAdvisory.model_validate_json(raw), trace
        incident_id = uuid4()
        advisory = OperatorAdvisory(
            incident_id=incident_id,
            severity="HIGH",
            target_zone_ids=[str(context.telemetry[0]["zone_id"])] if context.telemetry else ["unknown"],
            recommended_sop_id="SOP-CROWD-001",
            action_items=["Increase monitoring at the predicted bottleneck.", "Prepare alternate routing guidance."],
            confidence_score=0.78,
        )
        return advisory, {"mode": "deterministic", "generated_at": context.generated_at}
