import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .database import SessionLocal
from .models import Product, ScrapeJob, ScrapeResult, ScrapeResultItem
from .scraper import MARKETPLACES, build_search_url, scrape_marketplace, write_markdown
from .schemas import ScrapeJobCreate


def create_scrape_job(db: Session, payload: ScrapeJobCreate) -> ScrapeJob:
    product_ids = list(dict.fromkeys(payload.product_ids))
    marketplaces = list(dict.fromkeys(payload.marketplaces))
    if not product_ids:
        raise HTTPException(status_code=400, detail="Select at least one product")
    if not marketplaces:
        raise HTTPException(status_code=400, detail="Select at least one marketplace")

    products = list(db.execute(select(Product).where(Product.id.in_(product_ids))).scalars())
    found_ids = {product.id for product in products}
    missing = [str(product_id) for product_id in product_ids if product_id not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {', '.join(missing)}")

    missing_query = [product.sku for product in products if not product.search_query]
    if missing_query:
        raise HTTPException(status_code=400, detail=f"Products missing search_query: {', '.join(missing_query)}")

    job = ScrapeJob(
        requested_product_ids=[str(product_id) for product_id in product_ids],
        marketplaces=[str(marketplace) for marketplace in marketplaces],
        total_targets=len(products) * len(marketplaces),
    )
    db.add(job)
    db.flush()
    for product in products:
        for marketplace in marketplaces:
            db.add(
                ScrapeResult(
                    scrape_job_id=job.id,
                    product_id=product.id,
                    sku=product.sku,
                    marketplace=marketplace,
                    search_query=product.search_query or "",
                    search_url=build_search_url(marketplace, product.search_query or ""),
                    status="queued",
                )
            )
    db.commit()
    db.refresh(job)
    return job


def run_scrape_job(job_id: uuid.UUID, session_factory=SessionLocal) -> None:
    job_id = uuid.UUID(str(job_id))
    db = session_factory()
    try:
        job = db.get(ScrapeJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(UTC)
        db.commit()

        results = list(db.execute(select(ScrapeResult).where(ScrapeResult.scrape_job_id == job_id)).scalars())
        for result in results:
            result.status = "running"
            db.commit()
            error = None
            items = []
            try:
                items = scrape_marketplace(result.marketplace, result.search_url)
                result.status = "completed"
                result.result_count = len(items)
                db.add_all(
                    ScrapeResultItem(scrape_result_id=result.id, position=item.position, title=item.title, url=item.url)
                    for item in items
                )
                job.completed_targets += 1
            except Exception as exc:
                error = str(exc)
                result.status = "failed"
                result.error_message = error
                job.failed_targets += 1
            result.markdown_path = write_markdown(result.sku, result.marketplace, result.search_query, result.search_url, items, error)
            db.commit()

        job.completed_at = datetime.now(UTC)
        job.status = "completed_with_errors" if job.failed_targets else "completed"
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            job = db.get(ScrapeJob, job_id)
            if job:
                job.status = "failed"
                job.error_summary = str(exc)
                job.completed_at = datetime.now(UTC)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def get_scrape_job(db: Session, job_id: uuid.UUID) -> ScrapeJob:
    job = db.execute(
        select(ScrapeJob).where(ScrapeJob.id == job_id).options(selectinload(ScrapeJob.results).selectinload(ScrapeResult.items))
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job


def latest_product_scrape_results(db: Session, product_id: uuid.UUID) -> list[ScrapeResult]:
    return list(
        db.execute(
            select(ScrapeResult)
            .where(ScrapeResult.product_id == product_id)
            .options(selectinload(ScrapeResult.items))
            .order_by(ScrapeResult.created_at.desc())
        ).scalars()
    )
