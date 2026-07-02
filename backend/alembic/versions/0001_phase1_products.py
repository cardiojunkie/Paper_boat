"""phase1 products

Revision ID: 0001_phase1_products
Revises:
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_phase1_products"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("bullet_points", sa.Text(), nullable=True),
        sa.Column("specs", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("product_type", sa.String(length=255), nullable=True),
        sa.Column("attribute_set", sa.String(length=255), nullable=True),
        sa.Column("l1", sa.String(length=255), nullable=True),
        sa.Column("l2", sa.String(length=255), nullable=True),
        sa.Column("l3", sa.String(length=255), nullable=True),
        sa.Column("l4", sa.String(length=255), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_row", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_filename", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["sku", "category", "product_type", "attribute_set", "l1", "l2", "l3", "l4", "created_at", "updated_at"]:
        op.create_index(f"ix_products_{column}", "products", [column], unique=(column == "sku"))

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("inserted_rows", sa.Integer(), nullable=False),
        sa.Column("updated_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("warning_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_skus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("import_options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("initiating_user_identifier", sa.String(length=255), nullable=True),
        sa.CheckConstraint("status in ('processing','completed','failed')", name="ck_import_jobs_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "import_row_errors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("field_header", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_row_errors_import_job_id", "import_row_errors", ["import_job_id"])
    op.create_table(
        "sku_filter_tokens",
        sa.Column("token", sa.Uuid(), nullable=False),
        sa.Column("skus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_table(
        "deletion_audits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("operation_type", sa.String(length=64), nullable=False),
        sa.Column("applied_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("affected_count", sa.Integer(), nullable=False),
        sa.Column("explicit_skus", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("initiating_user_identifier", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("deletion_audits")
    op.drop_table("sku_filter_tokens")
    op.drop_index("ix_import_row_errors_import_job_id", table_name="import_row_errors")
    op.drop_table("import_row_errors")
    op.drop_table("import_jobs")
    for column in ["updated_at", "created_at", "l4", "l3", "l2", "l1", "attribute_set", "product_type", "category", "sku"]:
        op.drop_index(f"ix_products_{column}", table_name="products")
    op.drop_table("products")
