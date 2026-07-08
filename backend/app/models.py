import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from .database import Base

JsonType = JSONB().with_variant(JSON(), "sqlite")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    bullet_points: Mapped[str | None] = mapped_column(Text)
    specs: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    product_type: Mapped[str | None] = mapped_column(String(255), index=True)
    attribute_set: Mapped[str | None] = mapped_column(String(255), index=True)
    l1: Mapped[str | None] = mapped_column(String(255), index=True)
    l2: Mapped[str | None] = mapped_column(String(255), index=True)
    l3: Mapped[str | None] = mapped_column(String(255), index=True)
    l4: Mapped[str | None] = mapped_column(String(255), index=True)
    search_query: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    source_row: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (CheckConstraint("status in ('processing','completed','failed')", name="ck_import_jobs_status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_skus: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)
    import_options: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    initiating_user_identifier: Mapped[str | None] = mapped_column(String(255))
    errors: Mapped[list["ImportRowError"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ImportRowError(Base):
    __tablename__ = "import_row_errors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    field_header: Mapped[str | None] = mapped_column(String(255))
    job: Mapped[ImportJob] = relationship(back_populates="errors")


class SkuFilterToken(Base):
    __tablename__ = "sku_filter_tokens"

    token: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skus: Mapped[list[str]] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeletionAudit(Base):
    __tablename__ = "deletion_audits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    applied_filters: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    affected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    explicit_skus: Mapped[list[str] | None] = mapped_column(JsonType)
    snapshot: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    initiating_user_identifier: Mapped[str | None] = mapped_column(String(255))


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    __table_args__ = (
        CheckConstraint(
            "status in ('queued','running','completed','completed_with_errors','failed')",
            name="ck_scrape_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    requested_product_ids: Mapped[list[str]] = mapped_column(JsonType, nullable=False)
    marketplaces: Mapped[list[str]] = mapped_column(JsonType, nullable=False)
    total_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)
    initiating_user_identifier: Mapped[str | None] = mapped_column(String(255))
    results: Mapped[list["ScrapeResult"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ScrapeResult(Base):
    __tablename__ = "scrape_results"
    __table_args__ = (
        CheckConstraint("status in ('queued','running','completed','failed')", name="ck_scrape_results_status"),
        CheckConstraint(
            "match_status in ('pending','running','matched','no_match','failed')",
            name="ck_scrape_results_match_status",
        ),
        UniqueConstraint("product_id", "marketplace", name="uq_scrape_results_product_marketplace"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scrape_jobs.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    search_query: Mapped[str] = mapped_column(Text, nullable=False)
    search_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    markdown_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    match_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    matched_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    match_confidence: Mapped[int | None] = mapped_column(Integer)
    match_reason: Mapped[str | None] = mapped_column(Text)
    match_response: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    match_model: Mapped[str | None] = mapped_column(String(255))
    match_error_message: Mapped[str | None] = mapped_column(Text)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    job: Mapped[ScrapeJob] = relationship(back_populates="results")
    items: Mapped[list["ScrapeResultItem"]] = relationship(back_populates="result", cascade="all, delete-orphan")


class ScrapeResultItem(Base):
    __tablename__ = "scrape_result_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scrape_results.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[str | None] = mapped_column(Text)
    result: Mapped[ScrapeResult] = relationship(back_populates="items")


Index("ix_products_created_at", Product.created_at)
Index("ix_products_updated_at", Product.updated_at)
