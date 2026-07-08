import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .filters import FILTER_COLUMNS, apply_product_filters
from .matching import match_scrape_result
from .models import ImportJob, ImportRowError, Product, ScrapeResult
from .scrape_service import create_scrape_jobs, get_scrape_job, latest_product_scrape_results, run_scrape_jobs
from .scraper import MARKETPLACES
from .schemas import (
    BulkDeleteRequest,
    DeleteByFilterRequest,
    DeletePreviewRequest,
    DeletePreviewResponse,
    DeleteResponse,
    FilterOptionsResponse,
    ImportJobOut,
    ImportResult,
    OpenRouterSettingsOut,
    OpenRouterSettingsUpdate,
    ProductFilter,
    ProductListResponse,
    ProductOut,
    RowErrorOut,
    MarketplaceOut,
    ScrapeMarkdownOut,
    ScrapeMarkdownUpdate,
    ScrapeJobCreate,
    ScrapeJobCreated,
    ScrapeJobCreateResponse,
    ScrapeJobOut,
    ScrapeResultOut,
    SkuFileFilterResponse,
)
from .services import create_sku_filter, delete_products, import_products, preview_delete

router = APIRouter(prefix="/api")


def openrouter_settings() -> OpenRouterSettingsOut:
    return OpenRouterSettingsOut(configured=bool(settings.openrouter_api_key), model=settings.openrouter_model)


def scrape_markdown_path(result_id: uuid.UUID, db: Session) -> Path:
    result = db.execute(select(ScrapeResult).where(ScrapeResult.id == result_id)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Scrape result not found")
    if not result.markdown_path:
        raise HTTPException(status_code=404, detail="Markdown has not been generated")
    output_dir = Path(settings.scrape_output_dir).resolve()
    path = Path(result.markdown_path).resolve()
    if not path.is_relative_to(output_dir):
        raise HTTPException(status_code=404, detail="Markdown file not found")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")
    return path


def product_filters(
    sku_search: str | None = None,
    title_search: str | None = None,
    product_type: list[str] = Query(default=[]),
    attribute_set: list[str] = Query(default=[]),
    category: list[str] = Query(default=[]),
    l1: list[str] = Query(default=[]),
    l2: list[str] = Query(default=[]),
    l3: list[str] = Query(default=[]),
    l4: list[str] = Query(default=[]),
    sku_filter_token: uuid.UUID | None = None,
) -> ProductFilter:
    return ProductFilter(
        sku_search=sku_search,
        title_search=title_search,
        product_type=product_type,
        attribute_set=attribute_set,
        category=category,
        l1=l1,
        l2=l2,
        l3=l3,
        l4=l4,
        sku_filter_token=sku_filter_token,
    )


@router.get("/settings/openrouter", response_model=OpenRouterSettingsOut)
def get_openrouter_settings() -> OpenRouterSettingsOut:
    return openrouter_settings()


@router.put("/settings/openrouter", response_model=OpenRouterSettingsOut)
def update_openrouter_settings(payload: OpenRouterSettingsUpdate) -> OpenRouterSettingsOut:
    settings.openrouter_api_key = payload.api_key.strip() or None
    return openrouter_settings()


@router.post("/imports/products", response_model=ImportResult)
async def upload_products(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ImportJob:
    content = await file.read()
    job = import_products(db, content, file.filename or "upload.xlsx")
    return job


@router.get("/imports/{import_id}", response_model=ImportJobOut)
def get_import(import_id: uuid.UUID, db: Session = Depends(get_db)) -> ImportJob:
    job = db.get(ImportJob, import_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import not found")
    return job


@router.get("/imports/{import_id}/errors", response_model=list[RowErrorOut])
def get_import_errors(import_id: uuid.UUID, db: Session = Depends(get_db), page: int = 1, page_size: int = 100) -> list[ImportRowError]:
    return list(
        db.execute(
            select(ImportRowError)
            .where(ImportRowError.import_job_id == import_id)
            .order_by(ImportRowError.row_number)
            .offset((max(page, 1) - 1) * min(page_size, 500))
            .limit(min(page_size, 500))
        ).scalars()
    )


@router.get("/products", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    filters: ProductFilter = Depends(product_filters),
    page: int = 1,
    page_size: int = 50,
    sort: str = "updated_at",
    direction: str = "desc",
) -> ProductListResponse:
    sort_columns = {"sku": Product.sku, "title": Product.title, "created_at": Product.created_at, "updated_at": Product.updated_at}
    column = sort_columns.get(sort, Product.updated_at)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 250)
    base = apply_product_filters(select(Product), db, filters)
    total = int(db.execute(apply_product_filters(select(func.count()).select_from(Product), db, filters)).scalar_one())
    order = desc(column) if direction == "desc" else asc(column)
    items = list(db.execute(base.order_by(order).offset((page - 1) * page_size).limit(page_size)).scalars())
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/marketplaces", response_model=list[MarketplaceOut])
def marketplaces() -> list[MarketplaceOut]:
    return [MarketplaceOut(key=key, label=value["label"], enabled=True) for key, value in MARKETPLACES.items()]


@router.post("/scrape-jobs", response_model=ScrapeJobCreateResponse)
def start_scrape_job(
    payload: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ScrapeJobCreateResponse:
    jobs = create_scrape_jobs(db, payload)
    background_tasks.add_task(run_scrape_jobs, [job.id for job in jobs])
    return ScrapeJobCreateResponse(jobs=[ScrapeJobCreated(job_id=job.id, status=job.status) for job in jobs])


@router.get("/scrape-jobs/{job_id}", response_model=ScrapeJobOut)
def scrape_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_scrape_job(db, job_id)


@router.get("/products/filter-options", response_model=FilterOptionsResponse)
def product_filter_options(field: str, db: Session = Depends(get_db), filters: ProductFilter = Depends(product_filters)) -> FilterOptionsResponse:
    column = FILTER_COLUMNS.get(field)
    if column is None:
        raise HTTPException(status_code=400, detail="Unsupported filter field")
    stmt = apply_product_filters(select(column).where(column.is_not(None)).distinct().order_by(column).limit(500), db, filters)
    return FilterOptionsResponse(field=field, values=[value for value in db.execute(stmt).scalars() if value])


@router.get("/products/{product_id}", response_model=ProductOut)
def product_detail(product_id: uuid.UUID, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}/scrape-results", response_model=list[ScrapeResultOut])
def product_scrape_results(product_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ScrapeResult]:
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return latest_product_scrape_results(db, product_id)


@router.get("/scrape-results/{result_id}/markdown")
def scrape_result_markdown(result_id: uuid.UUID, db: Session = Depends(get_db)) -> FileResponse:
    path = scrape_markdown_path(result_id, db)
    return FileResponse(path, media_type="text/markdown")


@router.put("/scrape-results/{result_id}/markdown", response_model=ScrapeMarkdownOut)
def update_scrape_result_markdown(
    result_id: uuid.UUID, payload: ScrapeMarkdownUpdate, db: Session = Depends(get_db)
) -> ScrapeMarkdownOut:
    path = scrape_markdown_path(result_id, db)
    path.write_text(payload.content, encoding="utf-8")
    return ScrapeMarkdownOut(content=payload.content)


@router.post("/scrape-results/{result_id}/match", response_model=ScrapeResultOut)
def match_scrape_result_endpoint(result_id: uuid.UUID, db: Session = Depends(get_db)) -> ScrapeResult:
    return match_scrape_result(db, result_id)


@router.post("/product-filters/sku-file", response_model=SkuFileFilterResponse)
async def sku_filter_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> SkuFileFilterResponse:
    token, read_count, existing_count, errors = create_sku_filter(db, await file.read(), file.filename or "sku-filter.xlsx")
    return SkuFileFilterResponse(
        token=token.token,
        read_count=read_count,
        existing_count=existing_count,
        missing_count=read_count - existing_count,
        malformed_rows=[RowErrorOut(**error.__dict__) for error in errors],
    )


@router.delete("/products/{product_id}", response_model=DeleteResponse)
def delete_one(product_id: uuid.UUID, db: Session = Depends(get_db)) -> DeleteResponse:
    audit = delete_products(db, "single", ids=[product_id])
    return DeleteResponse(deleted_count=audit.affected_count, audit_id=audit.id)


@router.post("/products/bulk-delete", response_model=DeleteResponse)
def bulk_delete(payload: BulkDeleteRequest, db: Session = Depends(get_db)) -> DeleteResponse:
    count = len(payload.ids) + len(payload.skus)
    if count == 0:
        raise HTTPException(status_code=400, detail="No products selected")
    if payload.confirmation != f"DELETE {count} PRODUCTS":
        raise HTTPException(status_code=400, detail="Confirmation phrase did not match")
    audit = delete_products(db, "selected", ids=payload.ids, skus=payload.skus)
    return DeleteResponse(deleted_count=audit.affected_count, audit_id=audit.id)


@router.post("/products/delete-preview", response_model=DeletePreviewResponse)
def delete_preview(payload: DeletePreviewRequest, db: Session = Depends(get_db)) -> DeletePreviewResponse:
    count = preview_delete(db, payload.filters)
    return DeletePreviewResponse(count=count, confirmation_phrase=f"DELETE {count} PRODUCTS")


@router.post("/products/delete-by-filter", response_model=DeleteResponse)
def delete_by_filter(payload: DeleteByFilterRequest, db: Session = Depends(get_db)) -> DeleteResponse:
    count = preview_delete(db, payload.filters)
    if count != payload.expected_count:
        raise HTTPException(status_code=409, detail="Filter count changed; refresh preview")
    if payload.confirmation != f"DELETE {count} PRODUCTS":
        raise HTTPException(status_code=400, detail="Confirmation phrase did not match")
    audit = delete_products(db, "filter", filters=payload.filters)
    return DeleteResponse(deleted_count=audit.affected_count, audit_id=audit.id)
