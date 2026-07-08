import json
import uuid
from datetime import UTC, datetime
from typing import Literal, Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .models import Product, ScrapeResult, ScrapeResultItem


class CandidateDecision(BaseModel):
    item_id: str
    verdict: Literal["same", "different", "uncertain"]
    confidence: int = Field(ge=0, le=100)
    evidence: str
    mismatch_reason: str | None = None


class MatchDecision(BaseModel):
    decision: Literal["matched", "no_match"]
    matched_item_id: str | None = None
    confidence: int = Field(ge=0, le=100)
    reason: str
    candidates: list[CandidateDecision]


MATCH_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "product_match",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "decision": {"type": "string", "enum": ["matched", "no_match"]},
                "matched_item_id": {"type": ["string", "null"]},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                "reason": {"type": "string"},
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "item_id": {"type": "string"},
                            "verdict": {"type": "string", "enum": ["same", "different", "uncertain"]},
                            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                            "evidence": {"type": "string"},
                            "mismatch_reason": {"type": ["string", "null"]},
                        },
                        "required": ["item_id", "verdict", "confidence", "evidence", "mismatch_reason"],
                    },
                },
            },
            "required": ["decision", "matched_item_id", "confidence", "reason", "candidates"],
        },
    },
}


def _short(value: Any, limit: int = 500) -> str:
    text = str(value).strip()
    return text if len(text) <= limit else f"{text[:limit]}..."


def _clean_mapping(data: dict, limit: int = 40) -> dict[str, str]:
    cleaned = {}
    for key, value in data.items():
        if value not in (None, ""):
            cleaned[str(key)] = _short(value)
        if len(cleaned) >= limit:
            break
    return cleaned


def _match_input(product: Product, result: ScrapeResult, items: list[ScrapeResultItem]) -> dict:
    return {
        "product": {
            "sku": product.sku,
            "title": product.title,
            "bullet_points": product.bullet_points,
            "specs": product.specs,
            "category": product.category,
            "product_type": product.product_type,
            "attribute_set": product.attribute_set,
            "l1": product.l1,
            "l2": product.l2,
            "l3": product.l3,
            "l4": product.l4,
            "search_query": product.search_query,
            "attributes": _clean_mapping(product.attributes or {}),
            "source_row": _clean_mapping(product.source_row or {}),
        },
        "marketplace": result.marketplace,
        "candidates": [
            {
                "item_id": str(item.id),
                "position": item.position,
                "title": item.title,
                "price": item.price,
                "url": item.url,
            }
            for item in items
        ],
    }


def _messages(product: Product, result: ScrapeResult, items: list[ScrapeResultItem]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You match ecommerce products. Pick a candidate only if it is the same sellable product as the indexed "
                "product. Reject accessories, spare parts, bundles, different quantities, different capacities, different "
                "model numbers, and uncertain variants. If evidence is insufficient, return no_match."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(_match_input(product, result, items), ensure_ascii=False),
        },
    ]


def call_openrouter(messages: list[dict[str, str]], response_format: dict) -> dict:
    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "PickPilot",
        },
        json={
            "model": settings.openrouter_model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 2000,
            "provider": {"require_parameters": True},
            "response_format": response_format,
        },
        timeout=settings.openrouter_timeout_seconds,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content) if isinstance(content, str) else content


def _set_no_match(result: ScrapeResult, reason: str, response: dict | None = None) -> None:
    result.match_status = "no_match"
    result.matched_item_id = None
    result.match_confidence = 0
    result.match_reason = reason
    result.match_response = response or {"decision": "no_match", "reason": reason, "candidates": []}
    result.match_model = settings.openrouter_model
    result.match_error_message = None
    result.matched_at = datetime.now(UTC)


def _apply_decision(result: ScrapeResult, decision: MatchDecision, item_ids: set[str]) -> None:
    response = decision.model_dump()
    if decision.decision == "matched" and decision.matched_item_id in item_ids and decision.confidence >= 80:
        result.match_status = "matched"
        result.matched_item_id = uuid.UUID(decision.matched_item_id)
        result.match_confidence = decision.confidence
        result.match_reason = decision.reason
        result.match_response = response
        result.match_error_message = None
        result.matched_at = datetime.now(UTC)
        return
    _set_no_match(result, decision.reason, response)


def match_scrape_result(db: Session, result_id: uuid.UUID) -> ScrapeResult:
    result = db.execute(
        select(ScrapeResult).where(ScrapeResult.id == result_id).options(selectinload(ScrapeResult.items))
    ).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Scrape result not found")

    product = db.get(Product, result.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    items = sorted(result.items, key=lambda item: item.position)
    if not items:
        _set_no_match(result, "No scrape candidates to match")
        db.commit()
        db.refresh(result)
        return result
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is not configured")

    result.match_status = "running"
    result.matched_item_id = None
    result.match_confidence = None
    result.match_reason = None
    result.match_error_message = None
    result.match_model = settings.openrouter_model
    db.commit()

    try:
        raw = call_openrouter(_messages(product, result, items), MATCH_RESPONSE_FORMAT)
        decision = MatchDecision.model_validate(raw)
        _apply_decision(result, decision, {str(item.id) for item in items})
        result.match_model = settings.openrouter_model
    except (httpx.HTTPError, KeyError, TypeError, ValueError, ValidationError) as exc:
        result.match_status = "failed"
        result.matched_item_id = None
        result.match_confidence = None
        result.match_reason = None
        result.match_response = {}
        result.match_model = settings.openrouter_model
        result.match_error_message = str(exc)
        result.matched_at = datetime.now(UTC)
    db.commit()
    db.refresh(result)
    return result
