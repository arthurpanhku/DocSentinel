"""add tenant boundaries and trustworthy audit identity

Revision ID: 8d4e7c91b203
Revises: 2f6c5f07a101
Create Date: 2026-09-03
"""

from collections.abc import Sequence
from hashlib import sha256

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "8d4e7c91b203"
down_revision: str | Sequence[str] | None = "2f6c5f07a101"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tenant_type = sqlmodel.sql.sqltypes.AutoString(length=128)
    op.add_column(
        "user",
        sa.Column("tenant_id", tenant_type, nullable=False, server_default="default"),
    )
    op.create_index("ix_user_tenant_id", "user", ["tenant_id"])

    op.add_column(
        "projects",
        sa.Column("tenant_id", tenant_type, nullable=False, server_default="default"),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])

    for table_name in ("org_framework_configs", "policy_documents"):
        op.add_column(
            table_name,
            sa.Column(
                "tenant_id",
                tenant_type,
                nullable=False,
                server_default="default",
            ),
        )
        op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"])

    with op.batch_alter_table("gate_submissions") as batch_op:
        batch_op.add_column(sa.Column("submitted_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_gate_submissions_submitted_by_id_user",
            "user",
            ["submitted_by_id"],
            ["id"],
        )

    op.add_column(
        "governance_audit_logs",
        sa.Column("tenant_id", tenant_type, nullable=False, server_default="default"),
    )
    op.add_column(
        "governance_audit_logs",
        sa.Column(
            "outcome", sa.String(length=32), nullable=False, server_default="success"
        ),
    )
    op.add_column(
        "governance_audit_logs",
        sa.Column("request_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "governance_audit_logs",
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "governance_audit_logs",
        sa.Column("event_hash", sa.String(length=64), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id FROM governance_audit_logs ORDER BY created_at ASC, id ASC")
    ).fetchall()
    previous_hash: str | None = None
    for (row_id,) in rows:
        event_hash = sha256(f"legacy:{row_id}:{previous_hash}".encode()).hexdigest()
        connection.execute(
            sa.text(
                "UPDATE governance_audit_logs "
                "SET previous_hash = :previous_hash, event_hash = :event_hash "
                "WHERE id = :row_id"
            ),
            {
                "previous_hash": previous_hash,
                "event_hash": event_hash,
                "row_id": row_id,
            },
        )
        previous_hash = event_hash

    with op.batch_alter_table("governance_audit_logs") as batch_op:
        batch_op.alter_column("event_hash", existing_type=sa.String(64), nullable=False)
    op.create_index(
        "ix_governance_audit_logs_tenant_id",
        "governance_audit_logs",
        ["tenant_id"],
    )
    op.create_index(
        "ix_governance_audit_logs_request_id",
        "governance_audit_logs",
        ["request_id"],
    )
    op.create_index(
        "ix_governance_audit_logs_event_hash",
        "governance_audit_logs",
        ["event_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_governance_audit_logs_event_hash",
        table_name="governance_audit_logs",
    )
    op.drop_index(
        "ix_governance_audit_logs_request_id",
        table_name="governance_audit_logs",
    )
    op.drop_index(
        "ix_governance_audit_logs_tenant_id",
        table_name="governance_audit_logs",
    )
    with op.batch_alter_table("governance_audit_logs") as batch_op:
        batch_op.drop_column("event_hash")
        batch_op.drop_column("previous_hash")
        batch_op.drop_column("request_id")
        batch_op.drop_column("outcome")
        batch_op.drop_column("tenant_id")

    with op.batch_alter_table("gate_submissions") as batch_op:
        batch_op.drop_constraint(
            "fk_gate_submissions_submitted_by_id_user",
            type_="foreignkey",
        )
        batch_op.drop_column("submitted_by_id")

    op.drop_index("ix_projects_tenant_id", table_name="projects")
    op.drop_column("projects", "tenant_id")
    for table_name in ("policy_documents", "org_framework_configs"):
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)
        op.drop_column(table_name, "tenant_id")
    op.drop_index("ix_user_tenant_id", table_name="user")
    op.drop_column("user", "tenant_id")
