from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, confloat

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AdvisoryState(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    IN_EXECUTION = "IN_EXECUTION"
    COMPLETED = "COMPLETED"
    OVERRIDDEN = "OVERRIDDEN"

class WeatherInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rain_mm: float = Field(default=0, ge=0)
    severity: float = Field(default=0, ge=0, le=1)

class ZoneStateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_id: str = Field(min_length=1, max_length=64)
    occupancy: float = Field(ge=0)
    max_capacity: float = Field(gt=0)
    inflow_rate: float = Field(ge=0)
    outflow_rate: float = Field(ge=0)
    base_travel_seconds: float = Field(default=30, ge=0)
    density_change_per_minute: float = Field(default=0)
    warning_threshold: float = Field(default=0.75, ge=0, le=1)
    critical_threshold: float = Field(default=0.90, ge=0, le=1)

class PropagationEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_zone_id: str
    target_zone_id: str

class PropagationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zones: list[ZoneStateIn] = Field(min_length=1, max_length=100)
    edges: list[PropagationEdge] = Field(max_length=500)
    weather: WeatherInput = Field(default_factory=WeatherInput)

class PropagationSegment(BaseModel):
    source_zone_id: str
    target_zone_id: str
    propagation_delay_seconds: float
    queue_delay_seconds: float
    travel_delay_seconds: float
    target_time_to_capacity_seconds: float | None
    effective_outflow_rate: float
    weather_exit_velocity_multiplier: float

class PropagationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    segments: list[PropagationSegment]

class RiskZoneIn(ZoneStateIn):
    pass

class RiskMatrixRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zones: list[RiskZoneIn] = Field(min_length=1, max_length=100)
    weather: WeatherInput = Field(default_factory=WeatherInput)
    weights: dict[str, float] | None = None

class RiskZoneResult(BaseModel):
    zone_id: str
    score: confloat(ge=0, le=1)
    hazard_state: str
    early_warning: bool
    density_ratio: float
    normalized_density_rate: float
    bottleneck_factor: float
    weather_severity: float

class RiskMatrixResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    results: list[RiskZoneResult]

class OperatorAdvisory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: UUID
    severity: Severity
    target_zone_ids: list[str] = Field(min_length=1, max_length=50)
    recommended_sop_id: str = Field(min_length=1, max_length=128)
    action_items: list[str] = Field(min_length=1, max_length=50)
    confidence_score: confloat(ge=0, le=1)

class AdvisoryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    advisory: OperatorAdvisory
    operator_id: str = Field(min_length=1, max_length=128)
    ambient_telemetry: dict = Field(default_factory=dict)
    llm_trace: dict = Field(default_factory=dict)

class AdvisoryTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_state: AdvisoryState
    operator_id: str = Field(min_length=1, max_length=128)
    ambient_telemetry: dict = Field(default_factory=dict)
    llm_trace: dict = Field(default_factory=dict)

class TelemetrySnapshotIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_id: str
    occupancy: int = Field(ge=0)
    inflow_rate: float = Field(ge=0)
    outflow_rate: float = Field(ge=0)
    density_ratio: float = Field(ge=0, le=1)
    weather_severity: float = Field(default=0, ge=0, le=1)
    source: str = Field(default="camera", max_length=64)

class AgentGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_ids: list[str] = Field(min_length=1, max_length=100)
    weather: dict = Field(default_factory=dict)
    gate_throughput: dict = Field(default_factory=dict)
    query: str = Field(min_length=1, max_length=1000)
    query_embedding: list[float] | None = None

class SOPContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_ids: list[str] = Field(min_length=1, max_length=100)
    weather: dict = Field(default_factory=dict)
    gate_throughput: dict = Field(default_factory=dict)
    query: str = Field(min_length=1, max_length=1000)
    query_embedding: list[float] | None = None
