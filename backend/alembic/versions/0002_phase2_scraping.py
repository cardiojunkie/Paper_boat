"""phase2 scraping

Revision ID: 0002_phase2_scraping
Revises: 0001_phase1_products
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase2_scraping"
down_revision = "0001_phase1_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("search_query", sa.Text(), nullable=True))
    op.create_table(
        "scrape_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_product_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("marketplaces", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total_targets", sa.Integer(), nullable=False),
        sa.Column("completed_targets", sa.Integer(), nullable=False),
        sa.Column("failed_targets", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("initiating_user_identifier", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "status in ('queued','running','completed','completed_with_errors','failed')",
            name="ck_scrape_jobs_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scrape_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scrape_job_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=False),
        sa.Column("marketplace", sa.String(length=64), nullable=False),
        sa.Column("search_query", sa.Text(), nullable=False),
        sa.Column("search_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("markdown_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('queued','running','completed','failed')", name="ck_scrape_results_status"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scrape_job_id"], ["scrape_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_results_scrape_job_id", "scrape_results", ["scrape_job_id"])
    op.create_index("ix_scrape_results_product_id", "scrape_results", ["product_id"])
    op.create_index("ix_scrape_results_marketplace", "scrape_results", ["marketplace"])
    op.create_table(
        "scrape_result_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scrape_result_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_result_id"], ["scrape_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_result_items_scrape_result_id", "scrape_result_items", ["scrape_result_id"])


def downgrade() -> None:
    op.drop_index("ix_scrape_result_items_scrape_result_id", table_name="scrape_result_items")
    op.drop_table("scrape_result_items")
    op.drop_index("ix_scrape_results_marketplace", table_name="scrape_results")
    op.drop_index("ix_scrape_results_product_id", table_name="scrape_results")
    op.drop_index("ix_scrape_results_scrape_job_id", table_name="scrape_results")
    op.drop_table("scrape_results")
    op.drop_table("scrape_jobs")
    op.drop_column("products", "search_query")
