from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    BaseProduct,
    EvaluateMatchRequest,
    EvaluateMatchResponse,
    LLMMatchResult,
    URLGenerationResponse,
)

app = FastAPI(title="Search-Based Product Matching API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mock_saved_products: list[BaseProduct] = []


@app.post("/api/products", response_model=BaseProduct)
def save_product(product: BaseProduct) -> BaseProduct:
    mock_saved_products.append(product)
    return product


@app.get("/api/generate-url", response_model=URLGenerationResponse)
def generate_url(name: str, brand: str) -> URLGenerationResponse:
    query = quote_plus(f"{brand} {name}")
    return URLGenerationResponse(
        amazon_ae_url=f"https://www.amazon.ae/s?k={query}",
        noon_url=f"https://www.noon.com/uae-en/search/?q={query}",
    )


@app.post("/api/evaluate-match", response_model=EvaluateMatchResponse)
def evaluate_match(payload: EvaluateMatchRequest) -> EvaluateMatchResponse:
    urls = generate_url(name=payload.product.name, brand=payload.product.brand)
    competitor = payload.competitor_target.strip().lower()

    if competitor == "noon":
        search_url = urls.noon_url
    elif competitor in {"amazon", "amazon ae", "amazon.ae"}:
        search_url = urls.amazon_ae_url
    else:
        search_url = f"https://uae.sharafdg.com/search/?q={quote_plus(payload.product.brand + ' ' + payload.product.name)}"

    scraped_results = [
        f"{payload.product.brand} {payload.product.name} - 128GB - AED 1,999",
        f"{payload.product.brand} {payload.product.name} Pro - AED 2,299",
        f"Alternative listing for {payload.product.name} by another seller - AED 1,899",
    ]

    llm_evaluation = LLMMatchResult(
        exact_match_found=True,
        matched_competitor_title=scraped_results[0],
        price=1999.0,
        confidence_score=0.95,
        reasoning="Top result matches brand and model wording exactly with aligned pricing.",
    )

    return EvaluateMatchResponse(
        search_url=search_url,
        scraped_results=scraped_results,
        llm_evaluation=llm_evaluation,
    )
