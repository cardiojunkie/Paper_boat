"""add scrape result item price

Revision ID: 0003_scrape_result_item_price
Revises: 0002_phase2_scraping
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_scrape_result_item_price"
down_revision = "0002_phase2_scraping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scrape_result_items", sa.Column("price", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scrape_result_items", "price")
