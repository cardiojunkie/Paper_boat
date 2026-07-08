import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .database import SessionLocal
from .matching import match_scrape_result
from .models import Product, ScrapeJob, ScrapeResult, ScrapeResultItem
from .scraper import MARKETPLACES, build_search_url, scrape_marketplace, write_markdown
from .schemas import ScrapeJobCreate


def create_scrape_jobs(db: Session, payload: ScrapeJobCreate) -> list[ScrapeJob]:
    product_ids = list(dict.fromkeys(payload.product_ids))
    marketplaces = list(dict.fromkeys(payload.marketplaces))
    if not product_ids:
        raise HTTPException(status_code=400, detail="Select at least one product")
    if not marketplaces:
        raise HTTPException(status_code=400, detail="Select at least one marketplace")

    products_by_id = {product.id: product for product in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars()}
    found_ids = set(products_by_id)
    missing = [str(product_id) for product_id in product_ids if product_id not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {', '.join(missing)}")
    products = [products_by_id[product_id] for product_id in product_ids]

    missing_query = [product.sku for product in products if not (product.search_query or product.title)]
    if missing_query:
        raise HTTPException(status_code=400, detail=f"Products missing search_query: {', '.join(missing_query)}")

    jobs = []
    for product in products:
        search_query = product.search_query or product.title or ""
        job = ScrapeJob(
            requested_product_ids=[str(product.id)],
            marketplaces=[str(marketplace) for marketplace in marketplaces],
            total_targets=len(marketplaces),
        )
        db.add(job)
        db.flush()
        jobs.append(job)
        for marketplace in marketplaces:
            result = db.execute(
                select(ScrapeResult).where(ScrapeResult.product_id == product.id, ScrapeResult.marketplace == marketplace)
            ).scalar_one_or_none()
            if result is None:
                db.add(
                    ScrapeResult(
                        scrape_job_id=job.id,
                        product_id=product.id,
                        sku=product.sku,
                        marketplace=marketplace,
                        search_query=search_query,
                        search_url=build_search_url(marketplace, search_query),
                        status="queued",
                    )
                )
            else:
                result.scrape_job_id = job.id
                result.sku = product.sku
                result.search_query = search_query
                result.search_url = build_search_url(marketplace, search_query)
                result.status = "queued"
                result.result_count = 0
                result.error_message = None
                result.match_status = "pending"
                result.matched_item_id = None
                result.match_confidence = None
                result.match_reason = None
                result.match_response = {}
                result.match_model = None
                result.match_error_message = None
                result.matched_at = None
                result.review_status = "pending"
                db.add(result)
    db.commit()
    for job in jobs:
        db.refresh(job)
    return jobs


def run_scrape_jobs(job_ids: list[uuid.UUID], session_factory=SessionLocal) -> None:
    for job_id in job_ids:
        run_scrape_job(job_id, session_factory)


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
            result.match_status = "pending"
            result.matched_item_id = None
            result.match_confidence = None
            result.match_reason = None
            result.match_response = {}
            result.match_model = None
            result.match_error_message = None
            result.matched_at = None
            result.review_status = "pending"
            db.execute(delete(ScrapeResultItem).where(ScrapeResultItem.scrape_result_id == result.id))
            db.commit()
            error = None
            items = []
            try:
                items = scrape_marketplace(result.marketplace, result.search_url)
                result.status = "completed"
                result.result_count = len(items)
                db.add_all(
                    ScrapeResultItem(scrape_result_id=result.id, position=item.position, title=item.title, url=item.url, price=item.price)
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
            if settings.match_auto_enabled and settings.openrouter_api_key and result.status == "completed":
                match_scrape_result(db, result.id)

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
