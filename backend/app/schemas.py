import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SortField = Literal["sku", "title", "created_at", "updated_at"]
SortDirection = Literal["asc", "desc"]


class ProductFilter(BaseModel):
    sku_search: str | None = None
    title_search: str | None = None
    product_type: list[str] = Field(default_factory=list)
    attribute_set: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)
    l1: list[str] = Field(default_factory=list)
    l2: list[str] = Field(default_factory=list)
    l3: list[str] = Field(default_factory=list)
    l4: list[str] = Field(default_factory=list)
    sku_filter_token: uuid.UUID | None = None

    def has_narrowing_filter(self) -> bool:
        data = self.model_dump()
        return any(bool(value) for value in data.values())


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    title: str | None
    bullet_points: str | None
    specs: str | None
    category: str | None
    product_type: str | None
    attribute_set: str | None
    l1: str | None
    l2: str | None
    l3: str | None
    l4: str | None
    search_query: str | None
    attributes: dict
    source_row: dict
    source_filename: str | None
    created_at: datetime
    updated_at: datetime


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    title: str | None
    category: str | None
    product_type: str | None
    attribute_set: str | None
    l1: str | None
    l2: str | None
    l3: str | None
    l4: str | None
    search_query: str | None
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    page_size: int


class RowErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    row_number: int
    sku: str | None
    error_code: str
    message: str
    field_header: str | None


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    status: str
    total_rows: int
    valid_rows: int
    inserted_rows: int
    updated_rows: int
    failed_rows: int
    warning_rows: int
    duplicate_skus: list
    started_at: datetime
    completed_at: datetime | None
    error_summary: str | None


class ImportResult(ImportJobOut):
    errors: list[RowErrorOut]


class FilterOptionsResponse(BaseModel):
    field: str
    values: list[str]


class SkuFileFilterResponse(BaseModel):
    token: uuid.UUID
    read_count: int
    existing_count: int
    missing_count: int
    malformed_rows: list[RowErrorOut]


class BulkDeleteRequest(BaseModel):
    ids: list[uuid.UUID] = Field(default_factory=list)
    skus: list[str] = Field(default_factory=list)
    confirmation: str


class DeletePreviewRequest(BaseModel):
    filters: ProductFilter


class DeletePreviewResponse(BaseModel):
    count: int
    confirmation_phrase: str


class DeleteByFilterRequest(BaseModel):
    filters: ProductFilter
    expected_count: int
    confirmation: str


class DeleteResponse(BaseModel):
    deleted_count: int
    audit_id: uuid.UUID | None = None


MarketplaceKey = Literal["amazon", "noon", "sharafdg", "carrefour"]


class MarketplaceOut(BaseModel):
    key: MarketplaceKey
    label: str
    enabled: bool = True


class ScrapeJobCreate(BaseModel):
    product_ids: list[uuid.UUID]
    marketplaces: list[MarketplaceKey]


class ScrapeJobCreated(BaseModel):
    job_id: uuid.UUID
    status: str


class ScrapeJobCreateResponse(BaseModel):
    jobs: list[ScrapeJobCreated]


class ScrapeMarkdownUpdate(BaseModel):
    content: str


class ScrapeMarkdownOut(BaseModel):
    content: str


class ScrapeResultItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    title: str
    url: str
    price: str | None


class ScrapeResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    marketplace: MarketplaceKey
    search_query: str
    search_url: str
    status: str
    result_count: int
    markdown_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    items: list[ScrapeResultItemOut] = Field(default_factory=list)


class ScrapeJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    requested_product_ids: list[str]
    marketplaces: list[str]
    total_targets: int
    completed_targets: int
    failed_targets: int
    started_at: datetime | None
    completed_at: datetime | None
    error_summary: str | None
    results: list[ScrapeResultOut] = Field(default_factory=list)
