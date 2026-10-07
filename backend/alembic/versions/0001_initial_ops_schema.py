from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_ops_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "zones",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("boundary", sa.Text(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("warning_threshold", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("critical_threshold", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute("ALTER TABLE zones ALTER COLUMN boundary TYPE geometry(POLYGON,4326) USING boundary::geometry")
    op.create_index("idx_zones_boundary_gist", "zones", ["boundary"], postgresql_using="gist")
    op.create_table(
        "gates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("zone_id", sa.String(64), sa.ForeignKey("zones.id")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("active_turnstiles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flow_capacity_limit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute("ALTER TABLE gates ALTER COLUMN location TYPE geometry(POINT,4326) USING location::geometry")
    op.create_index("idx_gates_location_gist", "gates", ["location"], postgresql_using="gist")
    op.execute("CREATE TYPE advisory_state AS ENUM ('PROPOSED','PENDING_APPROVAL','APPROVED','IN_EXECUTION','COMPLETED','OVERRIDDEN')")
    op.create_table(
        "telemetry_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zone_id", sa.String(64), nullable=False),
        sa.Column("occupancy", sa.Integer(), nullable=False),
        sa.Column("inflow_rate", sa.Float(), nullable=False),
        sa.Column("outflow_rate", sa.Float(), nullable=False),
        sa.Column("density_ratio", sa.Float(), nullable=False),
        sa.Column("weather_severity", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id", "captured_at"),
        postgresql_partition_by="RANGE (captured_at)",
    )
    op.execute("CREATE TABLE telemetry_snapshots_default (LIKE telemetry_snapshots INCLUDING ALL)")
    op.execute("ALTER TABLE telemetry_snapshots ATTACH PARTITION telemetry_snapshots_default DEFAULT")
    op.create_index("idx_telemetry_zone_captured", "telemetry_snapshots", ["zone_id", "captured_at"])
    op.execute("""
    DO $$
    DECLARE d date := CURRENT_DATE - 1;
    BEGIN
      FOR i IN 0..7 LOOP
        EXECUTE format(
          'CREATE TABLE IF NOT EXISTS telemetry_snapshots_%s PARTITION OF telemetry_snapshots FOR VALUES FROM (%L) TO (%L)',
          to_char(d + i, 'YYYY_MM_DD'), d + i, d + i + 1
        );
      END LOOP;
    END $$;
    """)
    op.create_table(
        "advisories",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("state", postgresql.ENUM(name="advisory_state"), nullable=False, server_default="PROPOSED"),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("target_zone_ids", postgresql.JSONB(), nullable=False),
        sa.Column("recommended_sop_id", sa.String(128), nullable=False),
        sa.Column("action_items", postgresql.JSONB(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("operator_id", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True)),
        sa.Column("operator_id", sa.String(128), nullable=False),
        sa.Column("action_taken", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ambient_telemetry", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("llm_reasoning_trace", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_audit_incident", "audit_logs", ["incident_id"])
    op.create_table(
        "sop_documents",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.execute("ALTER TABLE sop_documents ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

def downgrade():
    op.drop_table("sop_documents")
    op.drop_index("idx_audit_incident", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("advisories")
    op.drop_index("idx_telemetry_zone_captured", table_name="telemetry_snapshots")
    op.execute("DROP TABLE IF EXISTS telemetry_snapshots CASCADE")
    op.execute("DROP TYPE IF EXISTS advisory_state")
    op.drop_index("idx_gates_location_gist", table_name="gates")
    op.drop_table("gates")
    op.drop_index("idx_zones_boundary_gist", table_name="zones")
    op.drop_table("zones")
