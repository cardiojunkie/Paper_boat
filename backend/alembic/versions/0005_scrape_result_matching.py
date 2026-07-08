"""scrape result matching

Revision ID: 0005_scrape_result_matching
Revises: 0004_unique_scrape_result
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_scrape_result_matching"
down_revision = "0004_unique_scrape_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scrape_results",
        sa.Column("match_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.add_column("scrape_results", sa.Column("matched_item_id", sa.Uuid(), nullable=True))
    op.add_column("scrape_results", sa.Column("match_confidence", sa.Integer(), nullable=True))
    op.add_column("scrape_results", sa.Column("match_reason", sa.Text(), nullable=True))
    op.add_column(
        "scrape_results",
        sa.Column(
            "match_response",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("scrape_results", sa.Column("match_model", sa.String(length=255), nullable=True))
    op.add_column("scrape_results", sa.Column("match_error_message", sa.Text(), nullable=True))
    op.add_column("scrape_results", sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_scrape_results_match_status",
        "scrape_results",
        "match_status in ('pending','running','matched','no_match','failed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_scrape_results_match_status", "scrape_results", type_="check")
    op.drop_column("scrape_results", "matched_at")
    op.drop_column("scrape_results", "match_error_message")
    op.drop_column("scrape_results", "match_model")
    op.drop_column("scrape_results", "match_response")
    op.drop_column("scrape_results", "match_reason")
    op.drop_column("scrape_results", "match_confidence")
    op.drop_column("scrape_results", "matched_item_id")
    op.drop_column("scrape_results", "match_status")
