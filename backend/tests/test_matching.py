from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Product, ScrapeJob, ScrapeResult, ScrapeResultItem


def _scrape_result(db: Session, with_item: bool = True) -> tuple[ScrapeResult, list[ScrapeResultItem]]:
    product = Product(
        sku="SKU1",
        title="Acme Washer 8kg Model X",
        bullet_points="8kg front load washer",
        specs="Model X, 8kg, white",
        attributes={"Brand": "Acme"},
        source_row={"Model": "X", "Capacity": "8kg"},
    )
    job = ScrapeJob(requested_product_ids=[], marketplaces=["amazon"], total_targets=1)
    db.add_all([product, job])
    db.flush()
    result = ScrapeResult(
        scrape_job_id=job.id,
        product_id=product.id,
        sku=product.sku,
        marketplace="amazon",
        search_query="Acme Washer Model X",
        search_url="https://example.test/search",
        status="completed",
    )
    db.add(result)
    db.flush()
    items = []
    if with_item:
        items = [
            ScrapeResultItem(
                scrape_result_id=result.id,
                position=1,
                title="Acme Model X 8kg Front Load Washing Machine",
                url="https://example.test/p/1",
                price="AED 999",
            )
        ]
        db.add_all(items)
    db.commit()
    return result, items


def test_openrouter_settings_api_does_not_expose_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "openrouter_model", "test-model")

    response = client.get("/api/settings/openrouter")
    assert response.status_code == 200
    assert response.json() == {"configured": False, "model": "test-model"}

    response = client.put("/api/settings/openrouter", json={"api_key": " test-key "})
    assert response.status_code == 200
    assert response.json() == {"configured": True, "model": "test-model"}
    assert "api_key" not in response.json()
    assert settings.openrouter_api_key == "test-key"

    response = client.put("/api/settings/openrouter", json={"api_key": "   "})
    assert response.status_code == 200
    assert response.json() == {"configured": False, "model": "test-model"}
    assert settings.openrouter_api_key is None


def test_manual_match_stores_suggestion(client: TestClient, db: Session, monkeypatch) -> None:
    from backend.app import matching

    result, items = _scrape_result(db)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "openrouter_model", "test-model")
    assert client.put("/api/settings/openrouter", json={"api_key": "test-key"}).status_code == 200

    def fake_openrouter(messages, response_format):
        assert response_format["type"] == "json_schema"
        assert "Acme Washer 8kg Model X" in messages[1]["content"]
        return {
            "decision": "matched",
            "matched_item_id": str(items[0].id),
            "confidence": 92,
            "reason": "Same brand, model, and capacity.",
            "candidates": [
                {
                    "item_id": str(items[0].id),
                    "verdict": "same",
                    "confidence": 92,
                    "evidence": "Brand/model/capacity align.",
                    "mismatch_reason": None,
                }
            ],
        }

    monkeypatch.setattr(matching, "call_openrouter", fake_openrouter)

    response = client.post(f"/api/scrape-results/{result.id}/match")

    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "matched"
    assert body["matched_item_id"] == str(items[0].id)
    assert body["match_confidence"] == 92
    assert body["match_model"] == "test-model"


def test_low_confidence_match_becomes_no_match(client: TestClient, db: Session, monkeypatch) -> None:
    from backend.app import matching

    result, items = _scrape_result(db)
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")

    def fake_openrouter(messages, response_format):
        return {
            "decision": "matched",
            "matched_item_id": str(items[0].id),
            "confidence": 60,
            "reason": "Similar title but variant is uncertain.",
            "candidates": [
                {
                    "item_id": str(items[0].id),
                    "verdict": "uncertain",
                    "confidence": 60,
                    "evidence": "Capacity appears similar.",
                    "mismatch_reason": "Model certainty is too low.",
                }
            ],
        }

    monkeypatch.setattr(matching, "call_openrouter", fake_openrouter)

    response = client.post(f"/api/scrape-results/{result.id}/match")

    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "no_match"
    assert body["matched_item_id"] is None


def test_match_requires_openrouter_key_when_candidates_exist(client: TestClient, db: Session, monkeypatch) -> None:
    result, _ = _scrape_result(db)
    monkeypatch.setattr(settings, "openrouter_api_key", None)

    response = client.post(f"/api/scrape-results/{result.id}/match")

    assert response.status_code == 400
    assert "OpenRouter API key" in response.json()["detail"]


def test_no_candidates_skips_llm(client: TestClient, db: Session, monkeypatch) -> None:
    from backend.app import matching

    result, _ = _scrape_result(db, with_item=False)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(matching, "call_openrouter", lambda messages, response_format: (_ for _ in ()).throw(AssertionError()))

    response = client.post(f"/api/scrape-results/{result.id}/match")

    assert response.status_code == 200
    assert response.json()["match_status"] == "no_match"


def test_successful_scrape_auto_runs_match(client: TestClient, db: Session, monkeypatch, tmp_path) -> None:
    from backend.app import api, scrape_service
    from backend.app.scraper import ScrapedItem

    product = Product(sku="SKU1", title="Washer", search_query="washer", attributes={}, source_row={})
    db.add(product)
    db.commit()
    called = []
    monkeypatch.setattr(settings, "scrape_output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "match_auto_enabled", True)
    monkeypatch.setattr(api, "run_scrape_jobs", lambda job_ids: None)
    monkeypatch.setattr(
        scrape_service,
        "scrape_marketplace",
        lambda marketplace, search_url: [ScrapedItem(1, "Washer", "https://example.test/p/1", "AED 10")],
    )

    def fake_match(db_arg, result_id):
        called.append(result_id)
        result = db_arg.get(ScrapeResult, result_id)
        result.match_status = "matched"
        return result

    monkeypatch.setattr(scrape_service, "match_scrape_result", fake_match)

    response = client.post("/api/scrape-jobs", json={"product_ids": [str(product.id)], "marketplaces": ["amazon"]})
    job_id = response.json()["jobs"][0]["job_id"]
    scrape_service.run_scrape_job(job_id, session_factory=lambda: db)

    assert called
