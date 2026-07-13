from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models import Product, ScrapeJob, ScrapeResult, ScrapeResultItem, SkuFilterToken
from backend.app.schemas import ProductFilter
from backend.app.services import import_products, preview_delete
from backend.tests.conftest import workbook_bytes, xls_workbook_bytes


def test_import_insert_then_replace_removes_stale_attributes(db: Session) -> None:
    first = workbook_bytes(
        ["SKU", "Title", "Product URL", "Search Query", "Color"],
        [["001", "Old", "https://store.test/old", "old query", "Blue"]],
    )
    second = workbook_bytes(["SKU", "Title", "search query", "Size"], [["001", "New", "new query", "Large"]])

    first_job = import_products(db, first, "first.xlsx")
    product = db.execute(select(Product).where(Product.sku == "001")).scalar_one()
    assert product.product_url == "https://store.test/old"

    second_job = import_products(db, second, "second.xlsx")
    product = db.execute(select(Product).where(Product.sku == "001")).scalar_one()

    assert first_job.inserted_rows == 1
    assert second_job.updated_rows == 1
    assert product.title == "New"
    assert product.product_url is None
    assert product.search_query == "new query"
    assert product.attributes == {"Size": "Large"}


def test_import_uses_title_when_search_query_missing(db: Session) -> None:
    content = workbook_bytes(["SKU", "name"], [["001", "Fallback Name"]])

    import_products(db, content, "products.xlsx")
    product = db.execute(select(Product).where(Product.sku == "001")).scalar_one()

    assert product.title == "Fallback Name"
    assert product.search_query == "Fallback Name"


def test_product_listing_filter_and_detail(client: TestClient, db: Session) -> None:
    product = Product(sku="A1", title="Alpha", product_type="Phone", attributes={}, source_row={})
    db.add(product)
    db.add(Product(sku="B2", title="Beta", product_type="Laptop", attributes={}, source_row={}))
    db.commit()

    response = client.get("/api/products", params={"product_type": "Phone"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["sku"] == "A1"

    detail = client.get(f"/api/products/{product.id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Alpha"


def test_sku_filter_file_does_not_modify_products(client: TestClient, db: Session) -> None:
    db.add(Product(sku="001", title="Alpha", attributes={}, source_row={}))
    db.commit()
    content = workbook_bytes(["SKU"], [["001"], ["999"], [None]])

    response = client.post(
        "/api/product-filters/sku-file",
        files={"file": ("filter.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["read_count"] == 2
    assert body["existing_count"] == 1
    assert db.execute(select(Product)).scalars().all()[0].sku == "001"


def test_sku_filter_file_accepts_xls(client: TestClient, db: Session) -> None:
    db.add(Product(sku="00123", title="Legacy Washer", attributes={}, source_row={}))
    db.commit()

    response = client.post(
        "/api/product-filters/sku-file",
        files={"file": ("filter.xls", xls_workbook_bytes(), "application/vnd.ms-excel")},
    )

    assert response.status_code == 200
    assert response.json()["read_count"] == 1
    assert response.json()["existing_count"] == 1


def test_expired_sku_filter_matches_nothing(client: TestClient, db: Session) -> None:
    product = Product(sku="001", title="Alpha", attributes={}, source_row={})
    token = SkuFilterToken(skus=["001"], expires_at=datetime.now(UTC) - timedelta(seconds=1))
    db.add_all([product, token])
    db.commit()

    response = client.get("/api/products", params={"sku_filter_token": str(token.token)})

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_delete_by_empty_filter_rejected(db: Session) -> None:
    try:
        preview_delete(db, ProductFilter())
    except Exception as exc:
        assert getattr(exc, "status_code") == 400
    else:
        raise AssertionError("empty delete filter should fail")


def test_selected_bulk_delete(client: TestClient, db: Session) -> None:
    product = Product(sku="D1", title="Delete", attributes={}, source_row={})
    db.add(product)
    db.commit()

    response = client.post(
        "/api/products/bulk-delete",
        json={"ids": [str(product.id)], "skus": [], "confirmation": "DELETE 1 PRODUCTS"},
    )

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1
    assert db.execute(select(Product)).scalars().all() == []


def test_marketplaces_endpoint(client: TestClient) -> None:
    response = client.get("/api/marketplaces")

    assert response.status_code == 200
    assert {item["key"] for item in response.json()} == {"amazon", "noon", "sharafdg", "carrefour"}


def test_scrape_job_requires_search_query(client: TestClient, db: Session) -> None:
    product = Product(sku="NOQUERY", attributes={}, source_row={})
    db.add(product)
    db.commit()

    response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})

    assert response.status_code == 400
    assert "missing search_query" in response.json()["detail"]


def test_scrape_job_api_with_mocked_scraper(client: TestClient, db: Session, monkeypatch, tmp_path) -> None:
    from backend.app import api
    from backend.app import scrape_service
    from backend.app.config import settings
    from backend.app.scraper import ScrapedItem

    settings.scrape_output_dir = str(tmp_path)
    product = Product(sku="SKU/1", title="Washer", search_query="washing machine", attributes={}, source_row={})
    db.add(product)
    db.commit()

    def fake_scrape(marketplace: str, search_url: str) -> list[ScrapedItem]:
        return [ScrapedItem(1, f"{marketplace} washer", f"{search_url}&p=1", "AED 10.00")]

    monkeypatch.setattr(api, "run_scrape_jobs", lambda job_ids: None)
    monkeypatch.setattr(scrape_service, "scrape_marketplace", fake_scrape)
    response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})

    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert len(jobs) == 1
    job_id = jobs[0]["job_id"]
    scrape_service.run_scrape_job(job_id, session_factory=lambda: db)
    job = client.get(f"/api/scrape-jobs/{job_id}").json()
    assert job["status"] == "completed"
    assert job["completed_targets"] == 1

    results = client.get(f"/api/products/{product.id}/scrape-results").json()
    assert results[0]["marketplace"] == "amazon"
    assert results[0]["result_count"] == 1
    assert results[0]["items"][0]["title"] == "amazon washer"
    assert results[0]["items"][0]["price"] == "AED 10.00"

    markdown = client.get(f"/api/scrape-results/{results[0]['id']}/markdown")
    assert markdown.status_code == 200
    assert "SKU/1" in markdown.text
    assert "AED 10.00" in markdown.text


def test_scrape_job_empty_result_fails(db: Session, monkeypatch, tmp_path) -> None:
    from backend.app import scrape_service
    from backend.app.config import settings
    from backend.app.schemas import ScrapeJobCreate

    settings.scrape_output_dir = str(tmp_path)
    product = Product(sku="SKU1", title="Washer", search_query="washing machine", attributes={}, source_row={})
    db.add(product)
    db.commit()

    def fake_scrape(marketplace: str, search_url: str):
        return []

    monkeypatch.setattr(scrape_service, "scrape_marketplace", fake_scrape)
    job = scrape_service.create_scrape_jobs(db, ScrapeJobCreate(product_ids=[product.id], marketplaces=["amazon"]))[0]
    job_id = job.id
    TestingSession = sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)

    scrape_service.run_scrape_job(job_id, session_factory=TestingSession)
    db.expire_all()
    job = db.get(ScrapeJob, job_id)
    assert job
    assert job.status == "completed_with_errors"
    assert job.failed_targets == 1

    result = db.execute(select(ScrapeResult).where(ScrapeResult.scrape_job_id == job_id)).scalar_one()
    assert result.status == "failed"
    assert result.result_count == 0
    assert result.error_message
    assert "returned no product results" in result.error_message

    assert result.markdown_path
    markdown = tmp_path.joinpath("SKU1_amazon.md").read_text()
    assert "## Error" in markdown
    assert "returned no product results" in markdown


def test_scrape_markdown_can_be_edited(client: TestClient, db: Session, tmp_path, monkeypatch) -> None:
    from backend.app.config import settings

    monkeypatch.setattr(settings, "scrape_output_dir", str(tmp_path))
    path = tmp_path / "result.md"
    path.write_text("old markdown", encoding="utf-8")
    product = Product(sku="SKU1", title="Washer", attributes={}, source_row={})
    job = ScrapeJob(requested_product_ids=[], marketplaces=["amazon"], total_targets=1)
    db.add_all([product, job])
    db.flush()
    result = ScrapeResult(
        scrape_job_id=job.id,
        product_id=product.id,
        sku=product.sku,
        marketplace="amazon",
        search_query="washer",
        search_url="https://example.test/search",
        status="completed",
        markdown_path=str(path),
    )
    missing_markdown = ScrapeResult(
        scrape_job_id=job.id,
        product_id=product.id,
        sku=product.sku,
        marketplace="noon",
        search_query="washer",
        search_url="https://example.test/noon",
        status="queued",
    )
    db.add_all([result, missing_markdown])
    db.commit()

    assert client.get(f"/api/scrape-results/{result.id}/markdown").text == "old markdown"

    response = client.put(f"/api/scrape-results/{result.id}/markdown", json={"content": "edited markdown"})

    assert response.status_code == 200
    assert response.json()["content"] == "edited markdown"
    assert path.read_text(encoding="utf-8") == "edited markdown"
    assert client.get(f"/api/scrape-results/{result.id}/markdown").text == "edited markdown"
    assert client.put(f"/api/scrape-results/{missing_markdown.id}/markdown", json={"content": "new"}).status_code == 404


def test_scrape_markdown_outside_output_dir_is_blocked(client: TestClient, db: Session, tmp_path, monkeypatch) -> None:
    from backend.app.config import settings

    output_dir = tmp_path / "scrape_outputs"
    outside_path = tmp_path / "outside.md"
    output_dir.mkdir()
    outside_path.write_text("nope", encoding="utf-8")
    monkeypatch.setattr(settings, "scrape_output_dir", str(output_dir))
    product = Product(sku="SKU1", title="Washer", attributes={}, source_row={})
    job = ScrapeJob(requested_product_ids=[], marketplaces=["amazon"], total_targets=1)
    db.add_all([product, job])
    db.flush()
    result = ScrapeResult(
        scrape_job_id=job.id,
        product_id=product.id,
        sku=product.sku,
        marketplace="amazon",
        search_query="washer",
        search_url="https://example.test/search",
        status="completed",
        markdown_path=str(outside_path),
    )
    db.add(result)
    db.commit()

    assert client.get(f"/api/scrape-results/{result.id}/markdown").status_code == 404
    assert client.put(f"/api/scrape-results/{result.id}/markdown", json={"content": "edited"}).status_code == 404
    assert outside_path.read_text(encoding="utf-8") == "nope"


def test_scrape_job_creation_is_one_job_per_sku(client: TestClient, db: Session, monkeypatch) -> None:
    from backend.app import api

    products = [
        Product(sku="SKU1", title="Washer 1", attributes={}, source_row={}),
        Product(sku="SKU2", title="Washer 2", attributes={}, source_row={}),
    ]
    db.add_all(products)
    db.commit()

    monkeypatch.setattr(api, "run_scrape_jobs", lambda job_ids: None)
    response = client.post(
        "/api/scrape-jobs",
        json={"product_ids": [str(product.id) for product in products], "marketplaces": ["amazon", "noon"]},
    )

    assert response.status_code == 200
    assert len(response.json()["jobs"]) == 2


def test_rescrape_reuses_product_marketplace_result(client: TestClient, db: Session, monkeypatch, tmp_path) -> None:
    from backend.app import api
    from backend.app import scrape_service
    from backend.app.config import settings
    from backend.app.scraper import ScrapedItem

    settings.scrape_output_dir = str(tmp_path)
    product = Product(sku="SKU1", title="Washer", search_query="washing machine", attributes={}, source_row={})
    db.add(product)
    db.commit()
    calls = 0

    def fake_scrape(marketplace: str, search_url: str) -> list[ScrapedItem]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return [ScrapedItem(1, "old washer", f"{search_url}&old=1"), ScrapedItem(2, "stale washer", f"{search_url}&old=2")]
        return [ScrapedItem(1, "new washer", f"{search_url}&new=1")]

    def start_scrape() -> str:
        response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})
        assert response.status_code == 200
        job_id = response.json()["jobs"][0]["job_id"]
        scrape_service.run_scrape_job(job_id, session_factory=lambda: db)
        return job_id

    monkeypatch.setattr(api, "run_scrape_jobs", lambda job_ids: None)
    monkeypatch.setattr(scrape_service, "scrape_marketplace", fake_scrape)
    first_job_id = start_scrape()
    first_result = db.execute(
        select(ScrapeResult).where(ScrapeResult.product_id == product.id, ScrapeResult.marketplace == "amazon")
    ).scalar_one()
    first_result_id = first_result.id
    first_markdown_path = first_result.markdown_path

    second_job_id = start_scrape()
    results = db.execute(
        select(ScrapeResult).where(ScrapeResult.product_id == product.id, ScrapeResult.marketplace == "amazon")
    ).scalars().all()
    items = db.execute(select(ScrapeResultItem).where(ScrapeResultItem.scrape_result_id == first_result_id)).scalars().all()

    assert first_job_id != second_job_id
    assert len(results) == 1
    assert results[0].id == first_result_id
    assert str(results[0].scrape_job_id) == second_job_id
    assert results[0].markdown_path == first_markdown_path
    assert results[0].markdown_path and results[0].markdown_path.endswith("SKU1_amazon.md")
    assert [item.title for item in items] == ["new washer"]
