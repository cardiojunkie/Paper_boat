import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .config import settings
from .excel import ParseError, parse_xlsx
from .filters import apply_product_filters, count_products
from .models import DeletionAudit, ImportJob, ImportRowError, Product, SkuFilterToken
from .schemas import ProductFilter


CORE_NAMES = [
    "title",
    "bullet_points",
    "specs",
    "category",
    "product_type",
    "attribute_set",
    "l1",
    "l2",
    "l3",
    "l4",
    "search_query",
]


def _error_model(job_id: uuid.UUID, error: ParseError) -> ImportRowError:
    return ImportRowError(
        import_job_id=job_id,
        row_number=error.row_number,
        sku=error.sku,
        error_code=error.error_code,
        message=error.message,
        field_header=error.field_header,
    )


def _upsert_products(db: Session, values: list[dict[str, Any]], now: datetime) -> None:
    if not values:
        return
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = pg_insert(Product).values(values)
        update_cols = {name: getattr(stmt.excluded, name) for name in [*CORE_NAMES, "attributes", "source_row", "source_filename"]}
        update_cols["updated_at"] = now
        db.execute(stmt.on_conflict_do_update(index_elements=[Product.sku], set_=update_cols))
        return

    # ponytail: SQLite fallback keeps tests local; Postgres remains the production path.
    for payload in values:
        product = db.execute(select(Product).where(Product.sku == payload["sku"])).scalar_one_or_none()
        if product:
            for name in [*CORE_NAMES, "attributes", "source_row", "source_filename"]:
                setattr(product, name, payload[name])
            product.updated_at = now
        else:
            db.add(Product(**payload))


def import_products(db: Session, content: bytes, filename: str) -> ImportJob:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")

    job = ImportJob(original_filename=filename, status="processing", import_options={"mode": "replace"})
    db.add(job)
    db.flush()
    try:
        parsed = parse_xlsx(content, filename, settings.max_import_rows)
        job.total_rows = parsed.total_rows
        job.valid_rows = len(parsed.valid_rows)
        job.failed_rows = len(parsed.errors)
        job.duplicate_skus = parsed.duplicate_skus
        db.add_all(_error_model(job.id, error) for error in parsed.errors)

        incoming_skus = [row.sku for row in parsed.valid_rows]
        existing = set(db.execute(select(Product.sku).where(Product.sku.in_(incoming_skus))).scalars()) if incoming_skus else set()
        job.updated_rows = len(existing)
        job.inserted_rows = len(incoming_skus) - len(existing)

        now = datetime.now(UTC)
        for start in range(0, len(parsed.valid_rows), settings.import_batch_size):
            values: list[dict[str, Any]] = []
            for row in parsed.valid_rows[start : start + settings.import_batch_size]:
                payload = {
                    "id": uuid.uuid4(),
                    "sku": row.sku,
                    "attributes": row.attributes,
                    "source_row": row.source_row,
                    "source_filename": filename,
                    "created_at": now,
                    "updated_at": now,
                }
                payload.update({name: row.core.get(name) for name in CORE_NAMES})
                values.append(payload)
            _upsert_products(db, values, now)

        job.status = "completed"
        job.completed_at = now
        db.commit()
    except ValueError as exc:
        job.status = "failed"
        job.error_summary = str(exc)
        job.completed_at = datetime.now(UTC)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(job)
    return job


def create_sku_filter(db: Session, content: bytes, filename: str) -> tuple[SkuFilterToken, int, int, list[ParseError]]:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
    parsed = parse_xlsx(content, filename, settings.max_sku_filter_rows)
    skus = sorted({row.sku for row in parsed.valid_rows if row.sku})
    existing_count = int(db.execute(select(func.count()).select_from(Product).where(Product.sku.in_(skus))).scalar_one()) if skus else 0
    token = SkuFilterToken(
        skus=skus,
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.sku_filter_ttl_seconds),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token, len(skus), existing_count, parsed.errors


def delete_products(db: Session, operation_type: str, filters: ProductFilter | None = None, ids: list[uuid.UUID] | None = None, skus: list[str] | None = None) -> DeletionAudit:
    stmt = select(Product.sku)
    if filters:
        stmt = apply_product_filters(stmt, db, filters)
    if ids:
        stmt = stmt.where(Product.id.in_(ids))
    if skus:
        stmt = stmt.where(Product.sku.in_(skus))
    target_skus = list(db.execute(stmt).scalars())
    if not target_skus:
        audit = DeletionAudit(operation_type=operation_type, affected_count=0, applied_filters=(filters.model_dump(mode="json") if filters else {}), explicit_skus=skus or target_skus)
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit
    db.execute(delete(Product).where(Product.sku.in_(target_skus)))
    audit = DeletionAudit(
        operation_type=operation_type,
        affected_count=len(target_skus),
        applied_filters=filters.model_dump(mode="json") if filters else {},
        explicit_skus=target_skus[:1000],
        snapshot={"truncated": len(target_skus) > 1000},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def preview_delete(db: Session, filters: ProductFilter) -> int:
    if not filters.has_narrowing_filter():
        raise HTTPException(status_code=400, detail="At least one narrowing filter is required")
    return count_products(db, filters)
