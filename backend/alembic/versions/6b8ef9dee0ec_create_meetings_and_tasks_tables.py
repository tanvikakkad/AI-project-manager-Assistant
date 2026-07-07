"""create meetings and tasks tables

Revision ID: 6b8ef9dee0ec
Revises:
Create Date: 2026-07-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b8ef9dee0ec"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("meeting_time", sa.Time(), nullable=False),
        sa.Column("raw_notes", sa.Text(), nullable=False),
        sa.Column(
            "processing_status",
            postgresql.ENUM(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                name="processing_status",
            ),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meetings"),
    )
    op.create_index("ix_meetings_meeting_date", "meetings", ["meeting_date"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("meeting_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column(
            "priority",
            postgresql.ENUM("LOW", "MEDIUM", "HIGH", "URGENT", name="task_priority"),
            server_default=sa.text("'MEDIUM'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("TODO", "IN_PROGRESS", "DONE", name="task_status"),
            server_default=sa.text("'TODO'"),
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name="fk_tasks_meeting_id_meetings",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    op.create_index("ix_tasks_meeting_id", "tasks", ["meeting_id"])
    op.create_index("ix_tasks_owner", "tasks", ["owner"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_status", "tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_priority", table_name="tasks")
    op.drop_index("ix_tasks_owner", table_name="tasks")
    op.drop_index("ix_tasks_meeting_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_meetings_meeting_date", table_name="meetings")
    op.drop_table("meetings")

    postgresql.ENUM(name="task_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="task_priority").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="processing_status").drop(op.get_bind(), checkfirst=True)
