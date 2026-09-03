"""add durable assessment tasks

Revision ID: 2f6c5f07a101
Revises: ebcc5bce6929
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "2f6c5f07a101"
down_revision: str | Sequence[str] | None = "ebcc5bce6929"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_tasks",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column(
            "tenant_id",
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=False,
            server_default="default",
        ),
        sa.Column("submitted_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "idempotency_key",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "status", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False
        ),
        sa.Column("phase", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column(
            "source", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False
        ),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("task_id"),
    )
    for column in (
        "tenant_id",
        "submitted_by_id",
        "idempotency_key",
        "status",
        "phase",
        "source",
        "created_at",
        "updated_at",
    ):
        op.create_index(
            op.f(f"ix_assessment_tasks_{column}"),
            "assessment_tasks",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("assessment_tasks")
