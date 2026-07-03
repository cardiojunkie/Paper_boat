"""unique scrape result per product marketplace

Revision ID: 0004_unique_scrape_result
Revises: 0003_scrape_result_item_price
Create Date: 2026-07-03
"""

from alembic import op

revision = "0004_unique_scrape_result"
down_revision = "0003_scrape_result_item_price"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT id, row_number() OVER (
                PARTITION BY product_id, marketplace
                ORDER BY created_at DESC, updated_at DESC, id DESC
            ) AS rn
            FROM scrape_results
        )
        DELETE FROM scrape_results
        WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
        """
    )
    op.create_unique_constraint(
        "uq_scrape_results_product_marketplace",
        "scrape_results",
        ["product_id", "marketplace"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_scrape_results_product_marketplace", "scrape_results", type_="unique")
