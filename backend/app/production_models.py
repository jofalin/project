import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .production_db import Base
from .config import get_settings

class AdvisoryState(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    IN_EXECUTION = "IN_EXECUTION"
    COMPLETED = "COMPLETED"
    OVERRIDDEN = "OVERRIDDEN"

class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    boundary: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    warning_threshold: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    critical_threshold: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    gates: Mapped[list["Gate"]] = relationship(back_populates="zone")

class Gate(Base):
    __tablename__ = "gates"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("zones.id"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)
    active_turnstiles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flow_capacity_limit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    zone: Mapped[Zone | None] = relationship(back_populates="gates")

class TelemetrySnapshot(Base):
    __tablename__ = "telemetry_snapshots"
    __table_args__ = {"postgresql_partition_by": "RANGE (captured_at)"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, default=func.now())
    zone_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    occupancy: Mapped[int] = mapped_column(Integer, nullable=False)
    inflow_rate: Mapped[float] = mapped_column(Float, nullable=False)
    outflow_rate: Mapped[float] = mapped_column(Float, nullable=False)
    density_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    weather_severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="camera", nullable=False)

class Advisory(Base):
    __tablename__ = "advisories"
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    state: Mapped[AdvisoryState] = mapped_column(SAEnum(AdvisoryState, name="advisory_state"), default=AdvisoryState.PROPOSED, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    target_zone_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recommended_sop_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action_items: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    operator_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    operator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    ambient_telemetry: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    llm_reasoning_trace: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

class SOPDocument(Base):
    __tablename__ = "sop_documents"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(get_settings().embedding_dim))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
