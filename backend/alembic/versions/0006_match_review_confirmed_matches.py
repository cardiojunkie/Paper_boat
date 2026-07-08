"""match review confirmed matches

Revision ID: 0006_match_review
Revises: 0005_scrape_result_matching
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_match_review"
down_revision = "0005_scrape_result_matching"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("product_url", sa.Text(), nullable=True))
    op.add_column(
        "scrape_results",
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.create_check_constraint(
        "ck_scrape_results_review_status",
        "scrape_results",
        "review_status in ('pending','confirmed','denied')",
    )
    op.create_table(
        "confirmed_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("scrape_result_id", sa.Uuid(), nullable=True),
        sa.Column("scrape_result_item_id", sa.Uuid(), nullable=True),
        sa.Column("sku", sa.String(length=255), nullable=False),
        sa.Column("product_title", sa.Text(), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("marketplace", sa.String(length=64), nullable=False),
        sa.Column("competitor_title", sa.Text(), nullable=False),
        sa.Column("competitor_url", sa.Text(), nullable=False),
        sa.Column("price", sa.Text(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scrape_result_id"], ["scrape_results.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scrape_result_item_id"], ["scrape_result_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "marketplace", name="uq_confirmed_matches_product_marketplace"),
    )
    op.create_index("ix_confirmed_matches_product_id", "confirmed_matches", ["product_id"])
    op.create_index("ix_confirmed_matches_scrape_result_id", "confirmed_matches", ["scrape_result_id"])
    op.create_index("ix_confirmed_matches_marketplace", "confirmed_matches", ["marketplace"])


def downgrade() -> None:
    op.drop_index("ix_confirmed_matches_marketplace", table_name="confirmed_matches")
    op.drop_index("ix_confirmed_matches_scrape_result_id", table_name="confirmed_matches")
    op.drop_index("ix_confirmed_matches_product_id", table_name="confirmed_matches")
    op.drop_table("confirmed_matches")
    op.drop_constraint("ck_scrape_results_review_status", "scrape_results", type_="check")
    op.drop_column("scrape_results", "review_status")
    op.drop_column("products", "product_url")
