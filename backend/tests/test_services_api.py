from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Product, ScrapeResult
from backend.app.schemas import ProductFilter
from backend.app.services import import_products, preview_delete
from backend.tests.conftest import workbook_bytes


def test_import_insert_then_replace_removes_stale_attributes(db: Session) -> None:
    first = workbook_bytes(["SKU", "Title", "Search Query", "Color"], [["001", "Old", "old query", "Blue"]])
    second = workbook_bytes(["SKU", "Title", "search query", "Size"], [["001", "New", "new query", "Large"]])

    first_job = import_products(db, first, "first.xlsx")
    second_job = import_products(db, second, "second.xlsx")
    product = db.execute(select(Product).where(Product.sku == "001")).scalar_one()

    assert first_job.inserted_rows == 1
    assert second_job.updated_rows == 1
    assert product.title == "New"
    assert product.search_query == "new query"
    assert product.attributes == {"Size": "Large"}


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
    product = Product(sku="NOQUERY", title="No Query", attributes={}, source_row={})
    db.add(product)
    db.commit()

    response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})

    assert response.status_code == 400
    assert "missing search_query" in response.json()["detail"]


def test_scrape_job_api_with_mocked_scraper(client: TestClient, db: Session, monkeypatch, tmp_path) -> None:
    from backend.app import scrape_service
    from backend.app.config import settings
    from backend.app.scraper import ScrapedItem

    settings.scrape_output_dir = str(tmp_path)
    product = Product(sku="SKU/1", title="Washer", search_query="washing machine", attributes={}, source_row={})
    db.add(product)
    db.commit()

    def fake_scrape(marketplace: str, search_url: str) -> list[ScrapedItem]:
        return [ScrapedItem(1, f"{marketplace} washer", f"{search_url}&p=1")]

    monkeypatch.setattr(scrape_service, "scrape_marketplace", fake_scrape)
    response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    scrape_service.run_scrape_job(job_id, session_factory=lambda: db)
    job = client.get(f"/api/scrape-jobs/{job_id}").json()
    assert job["status"] == "completed"
    assert job["completed_targets"] == 1

    results = client.get(f"/api/products/{product.id}/scrape-results").json()
    assert results[0]["marketplace"] == "amazon"
    assert results[0]["result_count"] == 1
    assert results[0]["items"][0]["title"] == "amazon washer"

    markdown = client.get(f"/api/scrape-results/{results[0]['id']}/markdown")
    assert markdown.status_code == 200
    assert "SKU/1" in markdown.text
